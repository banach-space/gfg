#!/usr/bin/env bats
#==============================================================================
# Tests for `gfg commit-tree`
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
  new_tree_hash=$(../gfg/gfg write-tree)
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg commit-tree <tree-hash>'" {
  new_commit_hash=$(../gfg/gfg commit-tree $new_tree_hash -m "Test commit")

  output_gfg=$(../gfg/gfg cat-file -t $new_commit_hash)
  output_git=$(git cat-file -t $new_commit_hash)

  expected_output="commit"

  [ "$output_gfg" = "$expected_output" ]
  [ "$output_git" = "$expected_output" ]
}

@test "Test 'gfg commit-tree <tree-hash>' after 'gfg commit-tree <tree-hash>'" {
  # `commit-tree` after `commit-tree` will simply create a new commit. The the
  # commits will differ as the dates will be different
  new_commit_hash_1=$(../gfg/gfg commit-tree $new_tree_hash -m "Test commit")
  # Pause to make sure that timestamps are different
  sleep 1
  new_commit_hash_2=$(../gfg/gfg commit-tree $new_tree_hash -m "Test commit")

  expected_output="commit"

  output_gfg=$(../gfg/gfg cat-file -t $new_commit_hash_1)
  output_git=$(git cat-file -t $new_commit_hash_1)
  [ "$output_gfg" = "$expected_output" ]
  [ "$output_git" = "$expected_output" ]

  output_gfg=$(../gfg/gfg cat-file -t $new_commit_hash_2)
  output_git=$(git cat-file -t $new_commit_hash_2)
  [ "$output_gfg" = "$expected_output" ]
  [ "$output_git" = "$expected_output" ]

  [ "$new_commit_hash_1" != "$new_commit_hash_2" ]
}

@test "Test 'gfg commit-tree <tree-shortened-hash>'" {
  new_commit_hash=$(../gfg/gfg commit-tree ${new_tree_hash:0:5} -m "Test commit")

  output_gfg=$(../gfg/gfg cat-file -t $new_commit_hash)
  output_git=$(git cat-file -t $new_commit_hash)

  expected_output="commit"

  [ "$output_gfg" = "$expected_output" ]
  [ "$output_git" = "$expected_output" ]
}

@test "Test 'gfg commit-tree <incorrect-hash>'" {
  set +e
  output=$(../gfg/gfg commit-tree some-invalid-hash -m "Test commit")
  expected_output=$(git commit-tree some-invalid-hash -m "Test commit" 2>&1)
  set -e

  [ "$output" = "$expected_output" ]
}

@test "Test 'git cat-file -p' after 'gfg commit-tree <tree-hash>'" {
  new_commit_hash=$(../gfg/gfg commit-tree $new_tree_hash -m "Test commit")

  output_gfg=$(../gfg/gfg cat-file -p $new_commit_hash)
  output_git=$(git cat-file -p $new_commit_hash)
  [ "$output_gfg" = "$output_git" ]

  output_l1=$(git cat-file -p $new_commit_hash | sed -n "1p")
  expected_output="tree $new_tree_hash"
  [ "$output_l1" = "$expected_output" ]

  output_l2=$(git cat-file -p $new_commit_hash | sed -n "2p")
  expected_output="parent"
  [[ "$output_l2.*" =~ "$expected_output" ]]

  output_l3=$(git cat-file -p $new_commit_hash | sed -n "3p")
  expected_output="author GFG Test <gfg@gfg.test>"
  [[ "$output_l3.*" =~ "$expected_output" ]]

  output_l4=$(git cat-file -p $new_commit_hash | sed -n "4p")
  expected_output="committer GFG Test <gfg@gfg.test>"
  [[ "$output_l4.*" =~ "$expected_output" ]]

  output_l7=$(git cat-file -p $new_commit_hash | sed -n "7p")
  expected_output="Test commit"
  [[ "$output_l7.*" =~ "$expected_output" ]]
}
