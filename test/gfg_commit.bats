#!/usr/bin/env bats
#==============================================================================
# Tests for `gfg commit`
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
  echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-3

  ../gfg/gfg add test-dir-2/test-dir-3/*
  ../gfg/gfg commit -m "Test commit 2"
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'git cat-file -p' after 'gfg commit'" {
  head_commit_hash=$(git rev-parse HEAD)

  output_gfg=$(../gfg/gfg cat-file -p $head_commit_hash)
  output_git=$(git cat-file -p $head_commit_hash)
  [ "$output_gfg" = "$output_git" ]

  output_l1=$(git cat-file -p $head_commit_hash | sed -n "1p")
  expected_output="tree"
  [[ "$output_l1.*" =~ "$expected_output" ]]

  output_l2=$(git cat-file -p $head_commit_hash | sed -n "2p")
  expected_output="parent"
  [[ "$output_l2.*" =~ "$expected_output" ]]

  output_l3=$(git cat-file -p $head_commit_hash | sed -n "3p")
  expected_output="author GFG Test <gfg@gfg.test>"
  [[ "$output_l3.*" =~ "$expected_output" ]]

  output_l4=$(git cat-file -p $head_commit_hash | sed -n "4p")
  expected_output="committer GFG Test <gfg@gfg.test>"
  [[ "$output_l4.*" =~ "$expected_output" ]]

  output_l5=$(git cat-file -p $head_commit_hash | sed -n "5p")
  expected_output=""
  [ "$output_l5" = "$expected_output" ]

  output_l6=$(git cat-file -p $head_commit_hash | sed -n "6p")
  expected_output=""
  [ "$output_l6" = "$expected_output" ]

  output_l7=$(git cat-file -p $head_commit_hash | sed -n "7p")
  expected_output="Test commit 2"
  [[ "$output_l7.*" =~ "$expected_output" ]]
}
