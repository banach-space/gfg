#!/usr/bin/env bats
#==============================================================================
# Tests `gfg write-tree` for a repository with exisiting commits (so tree cache
# is _not_ empty)
#==============================================================================

setup()
{
  TEST_REPO_DIR="test_repo_dir"

  # Go outside the GFG repo
  cd ../../ || exit 1

  mkdir ${TEST_REPO_DIR} && cd ${TEST_REPO_DIR} || exit 1
  ../gfg/gfg init

  # Add two files that the tests will read
  touch gfg-test-file-1
  echo "1234" >> gfg-test-file-1

  mkdir test-dir-1
  touch test-dir-1/gfg-test-file-2
  echo "4321" >> test-dir-1/gfg-test-file-2

  ../gfg/gfg add gfg-test-file-1 test-dir-1/gfg-test-file-2

  # Dummy set-up to aid testing (without this `git commit` won't work)
  git config --local user.email "gfg@gfg.test"
  git config --local user.name "GFG Test"

  git commit -m "Test commit"

  mkdir -p test-dir-2/test-dir-3/
  touch test-dir-2/test-dir-3/gfg-test-file-3
  touch test-dir-2/test-dir-3/gfg-test-file-4
  touch test-dir-2/test-dir-3/gfg-test-file-5
  echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-3
  echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-4
  echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-5

  ../gfg/gfg add test-dir-2/test-dir-3/*
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg write-tree' - verify tree hash" {
  # Verify the tree hash as generated by the `gfg write-tree` command
  output=$(../gfg/gfg write-tree 2>&1)
  # Extracted by manually investigating the repo generated in setup()
  expected_output="fc924eceb1af0c158dc775f0e55c64f60a6c5325"

  [ "$output" = "$expected_output" ]
}

@test "Test 'gfg write-tree' - verify that the new tree exists" {
  ../gfg/gfg write-tree
  # Extracted by manually investigating the repo generated in setup()
  expected_output=""

  output_ls=$(ls .git/objects/fc/924eceb1af0c158dc775f0e55c64f60a6c5325)
  expected_ls=".git/objects/fc/924eceb1af0c158dc775f0e55c64f60a6c5325"
	[ "$output_ls" = "$expected_ls" ]
}

@test "Test 'gfg write-tree' followed by 'git commit'" {
  generated_tree_hash=$(../gfg/gfg write-tree 2>&1)

  git commit -m "Test commit"
  expected_tree_hash=$(git log --pretty=format:'%T' -1)

	[ "$generated_tree_hash" = "$expected_tree_hash" ]
}

@test "Test 'gfg write-tree' after 'gfg write-tree'" {
  generated_tree_hash=$(../gfg/gfg write-tree 2>&1)

  git commit -m "Test commit"
  expected_tree_hash=$(git log --pretty=format:'%T' -1)

	[ "$generated_tree_hash" = "$expected_tree_hash" ]

  # Repeating 'gfg write-tree' should make it print the same tree hash (no new
  # tree is created)
  generated_tree_hash=$(../gfg/gfg write-tree 2>&1)
	[ "$generated_tree_hash" = "$expected_tree_hash" ]
}

@test "Test 'git status' after 'gfg write-tree' + 'git commit'" {
  ../gfg/gfg write-tree

  # Before the commit, there should 3 files in the staging area
  before_commit_l1=$(git status --untracked-files=no --porcelain | sed -n "1p")
  before_commit_l2=$(git status --untracked-files=no --porcelain | sed -n "2p")
  before_commit_l3=$(git status --untracked-files=no --porcelain | sed -n "3p")
  before_commit_expected_l1="A  test-dir-2/test-dir-3/gfg-test-file-3"
  before_commit_expected_l2="A  test-dir-2/test-dir-3/gfg-test-file-4"
  before_commit_expected_l3="A  test-dir-2/test-dir-3/gfg-test-file-5"
	[ "$before_commit_l1" = "$before_commit_expected_l1" ]
	[ "$before_commit_l2" = "$before_commit_expected_l2" ]
	[ "$before_commit_l3" = "$before_commit_expected_l3" ]

  # After the commit, there should be no files in the staging area
  git commit -m "Some commit message"
  after_commit=$(git status --untracked-files=no --porcelain)
	[ "$after_commit" = "" ]
}
