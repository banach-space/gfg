#!/usr/bin/env bats
#==============================================================================
# Test GFG commands when run outside any Git repositories
#
# Any `gfg` (similarly to `git`) should fail if the current directory is
# not in a Git repository. This can only be tested outside any Git repository,
# so this test doesn't really fit in other files (which assume and require that
# `gfg` is run inside a Git repository).
#==============================================================================

setup()
{
  TEST_REPO_DIR="test_repo_dir"

  # Go outside the GFG repo
  cd ../../ || exit 1

  # Create a directory for the test
  mkdir ${TEST_REPO_DIR} && cd ${TEST_REPO_DIR} || exit 1
}

teardown()
{
  # Get out of ${TEST_REPO_DIR} and delete it
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}


@test "Test 'gfg add' in a non-repo directory" {
  touch file.txt

  set +e
  output=$(../gfg/gfg add file.txt 2>&1)
  set -e

  expected_output='fatal: not a git repository (or any of the parent directories): .git'
  printf 'output: <%s>\n' "$output"
  printf 'expected_output: <%s>\n' "$expected_output"
	[ "$output" = "$expected_output" ]
}
