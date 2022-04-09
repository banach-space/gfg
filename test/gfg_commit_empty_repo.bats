#!/usr/bin/env bats
#==============================================================================
# Tests `gfg commit` for a repository with no commits (the first commit will
# have no parent)
#==============================================================================

setup()
{
  TEST_REPO_DIR="test_repo_dir"

  # Go outside the GFG repo
  cd ../../ || exit 1

  mkdir ${TEST_REPO_DIR} && cd ${TEST_REPO_DIR} || exit 1
  ../gfg/gfg init

  # Add one file
  touch test_file_1
  echo "1234" >> test_file_1
  ../gfg/gfg add test_file_1

  # Dummy set-up to aid testing (without this `git commit` won't work)
  git config --local user.email "gfg@gfg.test"
  git config --local user.name "GFG Test"

  # Create the commit
  ../gfg/gfg commit -m "Test commit GFG"
}

teardown()
{
  cd ../ || exit 1
  rm -rf ${TEST_REPO_DIR}

  # Get back to the GFG repo
  cd gfg/test || exit 1
}

@test "Test 'gfg write-tree' - no commits" {
  head_commit_hash=$(git rev-parse HEAD)

  output_gfg=$(../gfg/gfg cat-file -p $head_commit_hash)
  output_git=$(git cat-file -p $head_commit_hash)
  [ "$output_gfg" = "$output_git" ]

  output_l1=$(git cat-file -p $head_commit_hash | sed -n "1p")
  expected_output="tree"
  [[ "$output_l1.*" =~ "$expected_output" ]]

  output_l2=$(git cat-file -p $head_commit_hash | sed -n "2p")
  expected_output="author GFG Test <gfg@gfg.test>"
  [[ "$output_l2.*" =~ "$expected_output" ]]

  output_l3=$(git cat-file -p $head_commit_hash | sed -n "3p")
  expected_output="committer GFG Test <gfg@gfg.test>"
  [[ "$output_l3.*" =~ "$expected_output" ]]

  output_l4=$(git cat-file -p $head_commit_hash | sed -n "4p")
  expected_output=""
  [ "$output_l4" = "$expected_output" ]

  output_l5=$(git cat-file -p $head_commit_hash | sed -n "5p")
  expected_output=""
  [ "$output_l5" = "$expected_output" ]

  output_l6=$(git cat-file -p $head_commit_hash | sed -n "6p")
  expected_output="Test commit GFG"
  [[ "$output_l6.*" =~ "$expected_output" ]]
}
