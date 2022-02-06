# test_repository.py
"""Unit tests for the GitRepository class

Note taht in `setUp`, a test Git repository is created with the
create_test_repo.sh script. Knowledge of the structure of that repository might
help in understanding the tests in this file.  This test repository is then
deleted  at the end of this suite (i.e. in `tearDown`).
"""

from shutil import rmtree
from pathlib import Path
import subprocess
import unittest
import git_repository

class TestGitRepositoryClass(unittest.TestCase):
    """Top unit test class for this module
    """

    def setUp(self):
        # Create a test repo
        with subprocess.Popen(["bash", "create_test_repo.sh", "."],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            self.test_repo_dir = Path(process.stdout.read().decode().strip('\n'))

        # Files from create_test_repo.sh
        self.test_file_1 = "gfg-test-file-1"
        self.test_file_2 = "gfg-test-file-2"

    def tearDown(self):
        # Remove the test repo
        rmtree(self.test_repo_dir)

    def test_repo_exists_sanity(self):
        """ Sanity check that the GitRepository correctly recognises a
        directory containing a Git repo
        """
        repo = git_repository.GitRepository.get_repo(".")
        self.assertTrue(repo is not None,
                        "Failed to obtain a repo.")

    def test_no_repo_exists_sanity(self):
        """ Sanity check that the GitRepository correctly recognises that
        a directory is not a Git repo
        """
        repo = git_repository.GitRepository.get_repo("../../")
        self.assertTrue(repo is None,
                        "This directory should not be a Git repository.")

    def test_git_config_sanity(self):
        """ Sanity check the repo's config file auto-generated when
        initialising the repo
        """
        repo = git_repository.GitRepository.get_repo(".")
        self.assertTrue(repo is not None,
                        "Failed to obtain a repo.")

        self.assertTrue(repo.git_config.has_section("core"))
        self.assertFalse(repo.git_config.has_section("Core"))

    def test_object_exists_sanity(self):
        """ Verify that GitRepository correctly fails to find
        _non_existing_ objects
        """
        repo = git_repository.GitRepository.get_repo(self.test_repo_dir)
        self.assertTrue(not repo.is_object_in_repo("not-a-git-hash"))


    def test_object_exists(self):
        """ Verify that GitRepository correctly finds _existing_ objects"""
        repo = git_repository.GitRepository.get_repo(self.test_repo_dir)

        # The hashes below were extraced from the first commit in the test repo

        # gfg-test-file-1
        self.assertTrue(repo.is_object_in_repo("81c545efebe5f57d4cab2ba9ec294c4b0cadf672"))
        self.assertTrue(repo.is_object_in_repo("81c5"))

        # The Git tree for the first commit
        self.assertTrue(repo.is_object_in_repo("78a93e16e05870b898c4605d766eb61be81847ce"))
        self.assertTrue(repo.is_object_in_repo("78a9"))


if __name__ == "__main__":
    unittest.main()
