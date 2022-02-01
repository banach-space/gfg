# test_object.py
"""Unit tests for the GitObject class

Note that in `setUp`, a test Git repository is created with the
create_test_repo.sh script. Knowledge of the structure of that repository might
help in understanding the tests in this file.  This test repository is then
deleted  at the end of this suite (i.e. in `tearDown`).
"""

from shutil import rmtree
from pathlib import Path
import subprocess
import unittest
import os
import git_object
import git_repository
import git_index

class TestGitRepositoryClass(unittest.TestCase):
    """Top unit test class for this module
    """

    def setUp(self):
        # Create a test repo
        with subprocess.Popen(["bash", "create_test_repo.sh", "."],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            self.test_repo_dir = Path(process.stdout.read().decode().strip('\n'))

        # Files from create_test_repo.sh
        repo_dir_1 = "./test-dir-1"
        repo_dir_2 = "./test-dir-2/test-dir-3"
        self.repo_dirs = [repo_dir_1, repo_dir_2]
        self.non_repo_dir = "./test-dir-2/test-dir-3/test-dir-4"

        index_path = os.path.join(self.test_repo_dir, ".git/index")
        self.index_file = git_index.IndexFile(index_path)
        self.repo = git_repository.GitRepository.get_repo("gfg-test-repo/")

        self.test_dir = os.getcwd()

    def tearDown(self):
        # Remove the test repo
        rmtree(self.test_repo_dir)

    def test_save_new_tree(self):
        """ Create and save a completely new tree
        """
        # Change the directory to the repo dir
        os.chdir(self.test_repo_dir)

        # Get blobs in this tree
        blobs_in_tree = self.index_file.get_blobs(self.non_repo_dir)
        # Get sub-dirs in this tree
        subtrees = self.index_file.get_subtrees(self.non_repo_dir)
        # Create a new tree object
        new_tree_object = git_object.GitTreeObject(self.repo, blobs=blobs_in_tree, trees=subtrees)

        # Verify that the object is bit present yet
        self.assertFalse(self.repo.is_object_in_repo(new_tree_object.object_hash))

        # Save the new tree to a file
        new_tree_object.save_to_file()

        # Verify that the object is now indeed present
        self.assertTrue(self.repo.is_object_in_repo(new_tree_object.object_hash))

        # Return to the original test dir
        os.chdir(self.test_dir)

    def test_save_existing_tree(self):
        """ Saving a tree that already exists (should result in an error)
        """
        for dir_path in self.repo_dirs:
            # Change the directory to the repo dir
            os.chdir(self.test_repo_dir)

            # Get blobs in this tree
            blobs_in_tree = self.index_file.get_blobs(dir_path)
            # Get sub-dirs in this tree
            subtrees = self.index_file.get_subtrees(dir_path)
            # Create a new tree object
            new_tree_object = git_object.GitTreeObject(
                    self.repo, blobs=blobs_in_tree, trees=subtrees)

            # Trying to save the new tree should trigger an exception as this
            # tree already exists
            self.assertRaises(git_index.GFGError, new_tree_object.save_to_file)

            # Return to the original test dir
            os.chdir(self.test_dir)


if __name__ == "__main__":
    unittest.main()
