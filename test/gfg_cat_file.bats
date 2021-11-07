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
  hash_file_1=$(echo '1234' | git hash-object -w --stdin)

  touch test_file_2
  echo "4321" >> test_file_2
  hash_file_2=$(echo '4321' | git hash-object -w --stdin)

  ../gfg/gfg add test_file_1 test_file_2
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg cat-file blob <invalid-file>'" {

}

@test "Test 'gfg cat-file blob <file>'" {
  output=$(../gfg/gfg cat-file blob $hash_file_1)
  expected="1234"
	[ "$output" = "$expected" ]

  output=$(../gfg/gfg cat-file blob $hash_file_2)
  expected="4321"
	[ "$output" = "$expected" ]
}
