#! /bin/env bash
#==============================================================================
# Creates a basic test repository for Python unit tests.
#
#   INPUT: $1 - root directory in which to create the repository (default
#          value: ".")
#   OUTPUT: the name of the directory with the test repo (printed to stdout)
#==============================================================================
set -euo pipefail

# Currently prepared for testing `gfg write-tree`
readonly test_repo_dir="${1:-.}/gfg-test-repo/"

rm -rf "$test_repo_dir"
mkdir "$test_repo_dir" && cd "$test_repo_dir" || exit

git init --quiet

# Create the 1st file
touch gfg-test-file-1
echo "1234" >> gfg-test-file-1

# Create the 2nd file and 1st sub-dir
mkdir test-dir-1
touch test-dir-1/gfg-test-file-2
echo "4321" >> test-dir-1/gfg-test-file-2

# Create the 3rd file and 2nd sub-dir
mkdir -p test-dir-2/test-dir-3/
touch test-dir-2/test-dir-3/gfg-test-file-3
touch test-dir-2/test-dir-3/gfg-test-file-4
touch test-dir-2/test-dir-3/gfg-test-file-5
echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-3
echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-4
echo "4321" >> test-dir-2/test-dir-3/gfg-test-file-5

git add  gfg-test-file-1 test-dir-1/gfg-test-file-2 test-dir-2/test-dir-3/*

# Dummy set-up to aid testing (without this `git commit` won't work in remote
# CI)
git config --local user.email "gfg@gfg.test"
git config --local user.name "GFG Test"

git commit --quiet -m "First commit in test repo"

mkdir -p test-dir-2/test-dir-3/test-dir-4/

echo "$test_repo_dir"
