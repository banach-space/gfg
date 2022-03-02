#!/usr/bin/env bats
#==============================================================================
# Tests `gfg cat-file <object-type> <object-hash>`
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
  hash_file_1=$(echo '1234' | git hash-object --stdin)

  mkdir test_dir
  touch test_dir/test_file_2
  echo "4321" >> test_dir/test_file_2
  hash_file_2=$(echo '4321' | git hash-object --stdin)

  ../gfg/gfg add test_file_1 test_dir/test_file_2

  # Dummy set-up to aid testing (without this `git commit` won't work)
  git config --local user.email "gfg@gfg.test"
  git config --local user.name "GFG Test"

  git commit -m "Test commit"
  tree_hash=$(git log --pretty=format:'%T')
  commit_hash=$(git rev-parse HEAD)
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg log' vs 'git log" {
  invalid_object_hash="123456"

  set +e
  # Use `gfg log --disable-ascii-escape` rather than plain `gfg log` as
  # otherwise the presence of ASCII escape characters will cause the test to
  # fail. 
  # TODO: Figure out how to make `gfg log` auto-magically not to add ASCII
  # escape characters here.
  output=$(../gfg/gfg log --disable-ascii-escape 2>&1)
  expected_output=$(git log 2>&1)
  set -e

  # Trim trailing white-spaces
  output=`echo $output | xargs`
  expected_output=`echo $expected_output | xargs`

  [ "$output" = "$expected_output" ]
}
