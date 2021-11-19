#!/usr/bin/env bats
#==============================================================================
# Tests `gfg hash-object <file>`
#==============================================================================
setup()
{
  TEST_REPO_DIR="test_repo_dir"

  # Go outside the GFG repo
  cd ../../ || exit 1

  mkdir ${TEST_REPO_DIR} && cd ${TEST_REPO_DIR} || exit 1
  ../gfg/gfg init
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg hash-object <file>' vs 'git hash-object <file>'" {
  hash_file_1_git=$(echo '1234' | git hash-object --stdin)
  hash_file_1_gfg=$(echo '1234' | ../gfg/gfg hash-object --stdin)
	[ "$hash_file_1_git" = "$hash_file_1_gfg" ]

  hash_file_2_git=$(echo '4321' | git hash-object --stdin)
  hash_file_2_gfg=$(echo '4321' | ../gfg/gfg hash-object --stdin)
	[ "$hash_file_2_git" = "$hash_file_2_gfg" ]
}

@test "Test 'gfg hash-object -w <file>'" {
  # Generate the hash, but don't save the file in .git/objects
  hash_file=$(echo '1234' | ../gfg/gfg hash-object --stdin)
  file_name=".git/objects/${hash_file:0:2}/${hash_file:2:38}"

  set +e
  # This command should fail as the file is not present yet
  output_err=$(ls ${file_name} 2>&1)
  set -e
  # 1. Only use the final bit of the output. That's the only part that's
  # identical between Darwin and Linux:
  #   * Darwin: `ls: ${file_name}: No such file or directory`
  #   * Linux: `ls: cannot access '${file_name}': No such file or directory"
  # 2. Use `xargs` to trim white-spaces. The test won't pass otherwise:
  # https://stackoverflow.com/questions/369758/how-to-trim-whitespace-from-a-bash-variable
  output_err=`echo $output_err | awk -F':' '{ print $3 }' | xargs`
  expected_error="No such file or directory"
	[ "$output_err" = "$expected_error" ]

  # Generate the hash and save the file in .git/objects
  echo '1234' | ../gfg/gfg hash-object -w --stdin
  echo ${file_name}
  set +e
  output=$(ls ${file_name} 2>&1)
  set -e
  expected_error="${file_name}"
	[ "$output" = "$expected_error" ]
}
