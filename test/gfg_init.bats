#!/usr/bin/env bats
#==============================================================================
# Tests `gfg init`
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


@test "Test 'gfg init' + 'ls'" {
  output=$(ls .git/)
  expected_output=$'HEAD\nbranches\nconfig\ndescription\nobjects\nrefs'
  printf '<%s>\n' "$output"
  printf '<%s>\n' "$expected_output"
	[ "$output" = "$expected_output" ]
}

@test "Test 'gfg init' + 'git status'" {
  output=$(git status 2>&1)
  expected_output=$'On branch master\n\nNo commits yet\n\nnothing to commit'
  printf '<%s>\n' "$output"
  printf '<%s>\n' "$expected_output"
  # Depending on the version of Git that you use, there might be an extra note
  # at the end of `git status` when run in an empty repo: "(create/copy files
  # and use "git add" to track)". Here, I only make sure that the _beginning_ of
  # $output (i.e. `git status`) matches $expected_output.
	[[ "$output.*" =~ "$expected_output" ]]
}

@test "Test 'gfg init' + 'git log'" {
  set +e
  output=$(git log 2>&1)
  set -e
  expected_output="fatal: your current branch 'master' does not have any commits yet"

  printf '<%s>\n' "$output"
  printf '<%s>\n' "$expected_output"

	[ "$output" = "$expected_output" ]
}

@test "Test 'gfg init' + 'gfg init'" {
  output=$(../gfg/gfg init 2>&1)
  expected_output="Reinitialized existing Git repository in ${PWD}/.git/"

  printf 'output = <%s>\n' "$output"
  printf 'expected_output = <%s>\n' "$expected_output"

	[ "$output" = "$expected_output" ]
}

@test "Test 'gfg init' + 'git init'" {
  expected_output="Reinitialized existing Git repository in ${PWD}/.git/"
  output=$(git init 2>&1)

  printf 'output = <%s>\n' "$output"
  printf 'expected_output = <%s>\n' "$expected_output"

	[ "$output" = "$expected_output" ]
}

@test "Test 'gfg init' in subdirectory" {
  readonly sub_dir="sub_dir"
  mkdir ${sub_dir} && pushd ${sub_dir} || exit 1

  output=$(../../gfg/gfg init 2>&1)
  expected_output="Initialized empty Git repository in ${PWD}/${sub_dir}/.git"

  printf 'output = <%s>\n' "$output"
  printf 'expected_output = <%s>\n' "$expected_output"

	[ "$output" != "$expected_output" ]

  # Leave ${sub_dir}
  popd || exit 1
}
