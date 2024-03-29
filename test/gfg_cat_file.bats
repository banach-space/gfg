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

@test "Test 'gfg cat-file -p <file>'" {
  output=$(../gfg/gfg cat-file -p $hash_file_1)
  expected="1234"
  [ "$output" = "$expected" ]

  output=$(../gfg/gfg cat-file -p $hash_file_2)
  expected="4321"
  [ "$output" = "$expected" ]
}

@test "Test 'gfg cat-file -p <tree-hash>' vs 'git cat-file -p <tree-hash>" {
  output=$(../gfg/gfg cat-file -p $tree_hash)
  expected_output=$(cat <<-END
100644 blob 81c545efebe5f57d4cab2ba9ec294c4b0cadf672     test_file_1
040000 tree 031d5285a4c23b0fd4f6f0bdbe6cbce080ea0d9b     test_dir
END
)

  # Trim trailing white-spaces
  output=`echo $output | xargs`
  expected_output=`echo $expected_output | xargs`

  [ "$output" = "$expected_output" ]
}

@test "Test 'gfg cat-file -p <commit-hash>' vs 'git cat-file -p <commit-hash>" {
  output=$(../gfg/gfg cat-file -p $commit_hash)
  expected_output=$(git cat-file -p $commit_hash)
  echo $output
  echo $expected_output

  # Trim trailing white-spaces
  output=`echo $output | xargs`
  expected_output=`echo $expected_output | xargs`

  [ "$output" = "$expected_output" ]
}

@test "Test 'gfg cat-file -t <blob|tree_hash|commit-hash>'" {
  output=$(../gfg/gfg cat-file -t $hash_file_1)
  expected="blob"
  [ "$output" = "$expected" ]

  output=$(../gfg/gfg cat-file -t $tree_hash)
  expected="tree"
  [ "$output" = "$expected" ]

  output=$(../gfg/gfg cat-file -t $commit_hash)
  expected="commit"
  [ "$output" = "$expected" ]
}

@test "Test 'gfg cat-file -t <blob|tree|commit-shortened-hash>'" {
  output=$(../gfg/gfg cat-file -t ${hash_file_1:0:5})
  expected="blob"
  [ "$output" = "$expected" ]

  output=$(../gfg/gfg cat-file -t ${tree_hash:0:5})
  expected="tree"
  [ "$output" = "$expected" ]

  output=$(../gfg/gfg cat-file -t ${commit_hash:0:5})
  expected="commit"
  [ "$output" = "$expected" ]
}

@test "Test 'gfg cat-file blob <invalid-file>'" {
  invalid_file="invalid-file"
  set +e
  output=$(../gfg/gfg cat-file blob $invalid_file 2>&1)
  expected=$(git cat-file blob $invalid_file 2>&1)
  set -e
  [ "$output" = "$expected" ]
}

@test "Test 'gfg cat-file tree <invalid-tree>'" {
  invalid_tree="invalid-tree"

  set +e
  output=$(../gfg/gfg cat-file tree $invalid_tree 2>&1)
  expected=$(git cat-file tree $invalid_tree 2>&1)
  set -e
  [ "$output" = "$expected" ]
}

@test "Test 'gfg cat-file commit <invalid-commit>'" {
  invalid_commit="invalid-commit"

  set +e
  output=$(../gfg/gfg cat-file commit $invalid_commit 2>&1)
  expected=$(git cat-file commit $invalid_commit 2>&1)
  set -e
  [ "$output" = "$expected" ]
}

@test "Test 'gfg cat-file -p <invalid-object-hash>' vs 'git cat-file -p <invalid-object-hash>" {
  invalid_object_hash="123456"

  set +e
  output=$(../gfg/gfg cat-file -p $invalid_object_hash 2>&1)
  expected_output=$(git cat-file -p $invalid_object_hash 2>&1)
  set -e

  # Trim trailing white-spaces
  output=`echo $output | xargs`
  expected_output=`echo $expected_output | xargs`

  [ "$output" = "$expected_output" ]
}
