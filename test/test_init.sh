#!/usr/bin/env bats

setup()
{
  mkdir test_repo && cd test_repo
  ../../gfg init
}

teardown()
{
  cd ../
  rm -rf test_repo
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
  expected_output=$'On branch master\n\nNo commits yet\n\nnothing to commit (create/copy files and use "git add" to track)'
  printf '<%s>\n' "$output"
  printf '<%s>\n' "$expected_output"
	[ "$output" = "$expected_output" ]
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
  set +e
  output=$(../../gfg init 2>&1)
  set -e

  expected_output="Reinitialized existing Git repository in ${BATS_TEST_DIRNAME}/test_repo/.git/"
  printf '<%s>\n' "$output"
  printf '<%s>\n' "$expected_output"
	[ "$output" = "$expected_output" ]

  output=$(git init 2>&1)
  printf '<%s>\n' "$output"
  printf '<%s>\n' "$expected_output"
	[ "$output" = "$expected_output" ]
}
