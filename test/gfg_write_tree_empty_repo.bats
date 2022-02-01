#!/usr/bin/env bats
#==============================================================================
# Tests `gfg write-tree` for a repository with no commits (so tree cache is
# empty)
#==============================================================================

setup()
{
  TEST_REPO_DIR="test_repo_dir"

  # Go outside the GFG repo
  cd ../../ || exit 1

  mkdir ${TEST_REPO_DIR} && cd ${TEST_REPO_DIR} || exit 1
  ../gfg/gfg init

  # Add two files that the tests will read
  touch test_file_1
  echo "1234" >> test_file_1

  mkdir test_dir
  touch test_dir/test_file_2
  echo "4321" >> test_dir/test_file_2

  ../gfg/gfg add test_file_1 test_dir/test_file_2
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg write-tree' - no commits" {
  set +e
  output=$(../gfg/gfg write-tree 2>&1)
  set -e
  # Extracted by manually investigating the repo generated in setup()
  expected_output="ef07dd97668be8b37a746661bc1baa2fc3a200f0"
  echo $output

  [ "$output" = "$expected_output" ]
}
