#!/usr/bin/env bats
#==============================================================================
# Tests `gfg add`
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

@test "Test 'gfg add' for non-existent file" {
  set +e
  output_gfg=$(../gfg/gfg add random_file 2>&1)
  output_git=$(git add random_file 2>&1)
  set -e
  
  printf 'output_gfg: <%s>\n' "$output_gfg"
  printf 'output_git: <%s>\n' "$output_git"

	[ "$output_gfg" = "$output_git" ]
}

@test "Test 'gfg add file.txt' with 'git ls-files --debug --stage'" {
  # Checks the contents of the index after adding a file. `git add` and `gfg
  # add` should give identical results.
  touch file.txt

  ../gfg/gfg add file.txt
  output_after_gfg_l1=$(git ls-files --debug --stage | sed -n "1p")
  output_after_gfg_l2=$(git ls-files --debug --stage | sed -n "2p" | awk -F ':' '{print $2}')
  output_after_gfg_l3=$(git ls-files --debug --stage | sed -n "3p" | awk -F ':' '{print $2}')
  output_after_gfg_l4=$(git ls-files --debug --stage | sed -n "4p")
  output_after_gfg_l5=$(git ls-files --debug --stage | sed -n "5p")
  output_after_gfg_l6=$(git ls-files --debug --stage | sed -n "6p")
  git reset file.txt

  git add file.txt
  output_after_git_l1=$(git ls-files --debug --stage | sed -n "1p")
  output_after_git_l2=$(git ls-files --debug --stage | sed -n "2p" | awk -F ':' '{print $2}')
  output_after_git_l3=$(git ls-files --debug --stage | sed -n "3p" | awk -F ':' '{print $2}')
  output_after_git_l4=$(git ls-files --debug --stage | sed -n "4p")
  output_after_git_l5=$(git ls-files --debug --stage | sed -n "5p")
  output_after_git_l6=$(git ls-files --debug --stage | sed -n "6p")
  git reset file.txt

  printf 'output_gfg: <%s>\n' "$output_after_gfg_l1"
  printf 'output_git: <%s>\n' "$output_after_git_l1"

	[ "$output_after_gfg_l1" = "$output_after_git_l1" ]
	[ "$output_after_gfg_l2" = "$output_after_git_l2" ]
	[ "$output_after_gfg_l3" = "$output_after_git_l3" ]
	[ "$output_after_gfg_l4" = "$output_after_git_l4" ]
	[ "$output_after_gfg_l5" = "$output_after_git_l5" ]
	[ "$output_after_gfg_l6" = "$output_after_git_l6" ]
}

@test "Test 'gfg add file_1.txt file_2.txt' with 'git ls-files --debug --stage'" {
  # Checks the contents of the index after adding 2 files. `git add` and `gfg
  # add` should give identical results.
  touch file_1.txt
  echo "1234" >> file_1.txt
  touch file_2.txt
  echo "4321" >> file_2.txt

  ../gfg/gfg add file_1.txt file_2.txt
  # 1st file
  output_after_gfg_l1=$(git ls-files --debug --stage | sed -n "1p")
  output_after_gfg_l2=$(git ls-files --debug --stage | sed -n "2p" | awk -F ':' '{print $2}')
  output_after_gfg_l3=$(git ls-files --debug --stage | sed -n "3p" | awk -F ':' '{print $2}')
  output_after_gfg_l4=$(git ls-files --debug --stage | sed -n "4p")
  output_after_gfg_l5=$(git ls-files --debug --stage | sed -n "5p")
  output_after_gfg_l6=$(git ls-files --debug --stage | sed -n "6p")

  # 2nd file
  output_after_gfg_l7=$(git ls-files --debug --stage | sed -n "7p")
  output_after_gfg_l8=$(git ls-files --debug --stage | sed -n "8p" | awk -F ':' '{print $2}')
  output_after_gfg_l9=$(git ls-files --debug --stage | sed -n "9p" | awk -F ':' '{print $2}')
  output_after_gfg_l10=$(git ls-files --debug --stage | sed -n "10p")
  output_after_gfg_l11=$(git ls-files --debug --stage | sed -n "11p")
  output_after_gfg_l12=$(git ls-files --debug --stage | sed -n "12p")
  git reset file_1.txt file_2.txt

  git add file_1.txt file_2.txt
  # 1st file
  output_after_git_l1=$(git ls-files --debug --stage | sed -n "1p")
  output_after_git_l2=$(git ls-files --debug --stage | sed -n "2p" | awk -F ':' '{print $2}')
  output_after_git_l3=$(git ls-files --debug --stage | sed -n "3p" | awk -F ':' '{print $2}')
  output_after_git_l4=$(git ls-files --debug --stage | sed -n "4p")
  output_after_git_l5=$(git ls-files --debug --stage | sed -n "5p")
  output_after_git_l6=$(git ls-files --debug --stage | sed -n "6p")

  # 2nd file
  output_after_git_l7=$(git ls-files --debug --stage | sed -n "7p")
  output_after_git_l8=$(git ls-files --debug --stage | sed -n "8p" | awk -F ':' '{print $2}')
  output_after_git_l9=$(git ls-files --debug --stage | sed -n "9p" | awk -F ':' '{print $2}')
  output_after_git_l10=$(git ls-files --debug --stage | sed -n "10p")
  output_after_git_l11=$(git ls-files --debug --stage | sed -n "11p")
  output_after_git_l12=$(git ls-files --debug --stage | sed -n "12p")
  git reset file_1.txt file_2.txt

  printf 'output_gfg: <%s>\n' "$output_after_gfg_l1"
  printf 'output_git: <%s>\n' "$output_after_git_l1"

	[ "$output_after_gfg_l1" = "$output_after_git_l1" ]
	[ "$output_after_gfg_l2" = "$output_after_git_l2" ]
	[ "$output_after_gfg_l3" = "$output_after_git_l3" ]
	[ "$output_after_gfg_l4" = "$output_after_git_l4" ]
	[ "$output_after_gfg_l5" = "$output_after_git_l5" ]
	[ "$output_after_gfg_l6" = "$output_after_git_l6" ]
	[ "$output_after_gfg_l7" = "$output_after_git_l7" ]
	[ "$output_after_gfg_l8" = "$output_after_git_l8" ]
	[ "$output_after_gfg_l9" = "$output_after_git_l9" ]
	[ "$output_after_gfg_l10" = "$output_after_git_l10" ]
	[ "$output_after_gfg_l11" = "$output_after_git_l11" ]
	[ "$output_after_gfg_l12" = "$output_after_git_l12" ]
}

@test "Test 'gfg add <file>' followed by 'gfg add <file>'" {
  # Adding the same file twice is fine and should generate no output
  touch empty_test_file
  ../gfg/gfg add empty_test_file
  ../gfg/gfg add empty_test_file

  output=$(../gfg/gfg add empty_test_file)
  expected=""
	[ "$output" = "$expected" ]
}

@test "Test 'gfg add <file>' with 'ls .git/objects'" {
  # After `git add <file`, there should be a new object in `.git/objects`. Test
  # this for an empty file.
  touch empty_test_file
  ../gfg/gfg add empty_test_file

  output_git=$(git ls-files)
  expected_git="empty_test_file"
	[ "$output_git" = "$expected_git" ]

  # For given file contents, the hash value will always be the same.  You can
  # read here about the origins of this value:
  # https://alblue.bandlem.com/2011/08/git-tip-of-week-objects.html
  output_ls=$(ls .git/objects/e6/9de29bb2d1d6434b8b29ae775ad8c2e48c5391)
  expected_ls=".git/objects/e6/9de29bb2d1d6434b8b29ae775ad8c2e48c5391"
	[ "$output_ls" = "$expected_ls" ]
}

@test "Test 'gfg add <file>' with 'git show'" {
  touch test_file
  echo "1234" >> test_file
  ../gfg/gfg add test_file

  output_ls=$(ls .git/objects/81/c545efebe5f57d4cab2ba9ec294c4b0cadf672)
  expected_ls=".git/objects/81/c545efebe5f57d4cab2ba9ec294c4b0cadf672"
	[ "$output_ls" = "$expected_ls" ]

  git_show=$(git show 81c545efebe5f57d4cab2ba9ec294c4b0cadf672)
	[ "$git_show" = "1234" ]
}

@test "Test 'gfg add <file_1> <file_2>' with 'git show'" {
  touch test_file_1
  touch test_file_2
  echo "1234" >> test_file_1
  echo "4321" >> test_file_2
  ../gfg/gfg add test_file_1 test_file_2

  # test_file_1
  git_show=$(git show 81c545efebe5f57d4cab2ba9ec294c4b0cadf672)
	[ "$git_show" = "1234" ]

  # test_file_2
  git_show=$(git show 79ed404b9b839e31ab01724a986c7d67218c1471)
	[ "$git_show" = "4321" ]
}
