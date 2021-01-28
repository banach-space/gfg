# test_repository.py
"""Unit tests GitRepository
"""

import unittest
import repository

class TestGitRepositoryClass(unittest.TestCase):
    """Top unit test class for this module
    """

    def test_repo_exists_sanity(self):
        """ Sanity check that the GitRepository correctly recognises a
        directory containing a Git repo
        """
        repo = repository.GitRepository.get_repo(".")
        self.assertTrue(repo is not None,
                        "Failed to obtain a repo.")

    def test_no_repo_exists_sanity(self):
        """ Sanity check that the GitRepository correctly recognises that
        a directory is not a Git repo
        """
        repo = repository.GitRepository.get_repo("../../")
        self.assertTrue(repo is None,
                        "This directory should not be a Git repository.")

    def test_git_config_sanity(self):
        """ Sanity check the repo's config file auto-generated when
        initialising the repo
        """
        repo = repository.GitRepository.get_repo(".")
        self.assertTrue(repo is not None,
                        "Failed to obtain a repo.")

        self.assertTrue(repo.git_config.has_section("core"))
        self.assertFalse(repo.git_config.has_section("Core"))

if __name__ == "__main__":
    unittest.main()
