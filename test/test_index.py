# test_index.py
"""Unit tests for index-file related classes

Note taht in `setUp`, a test Git repository is created with the
create_test_repo.sh script. Knowledge of the structure of that repository might
help in understanding the tests in this file.  This test repository is then
deleted  at the end of this suite (i.e. in `tearDown`).
"""

from shutil import copyfile
from shutil import rmtree
import os
from pathlib import Path
import unittest
import hashlib
import subprocess
import git_index


class TestIndexClass(unittest.TestCase):
    """Top unit test class for this module

    """
    file_name_in = "index_test_in"
    file_name_out = "index_test_out"
    index_file = None

    def setUp(self):
        # Create a test repo
        with subprocess.Popen(["bash", "create_test_repo.sh", os.getcwd()],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            self.test_repo_dir = Path(process.stdout.read().decode().strip('\n'))
            self.assertTrue(os.path.exists(self.test_repo_dir))
            index_path = os.path.join(self.test_repo_dir, ".git/index")
            self.assertTrue(os.path.exists(index_path),
                    f'index_path = {str(index_path)}, repo_path = {self.test_repo_dir}')

        # Copy the index file of GFG and use that as input for tests
        index_path = os.path.join(self.test_repo_dir, ".git/index")
        self.assertTrue(os.path.exists(index_path))
        copyfile(index_path, self.file_name_in)
        self.index_file = git_index.IndexFile(self.file_name_in)

        # Parse the index file and validate it
        self.index_file.validate()

        # Files from create_test_repo.sh
        self.test_files = ["gfg-test-file-1", "gfg-test-file-2",
                "gfg-test-file-3", "gfg-test-file-4", "gfg-test-file-5"]

        # Dirs from create_test_repo.sh
        self.test_dirs = ["./test-dir-1", "./test-dir-2",
                "./test-dir-2/test-dir-3"]

    def tearDown(self):
        # Remove the test repo
        rmtree(self.test_repo_dir)

    def test_read_write_sanity(self):
        """Write index file - sanity check

        Saves a fresh copy of the index file based on the member variables. Verifies
        that the generated and the original files are identical.
        """
        # Save the input index file into the output file
        self.index_file.print_to_file(self.file_name_out)

        # Compare the two index files
        with open(self.file_name_in, "rb") as file_in, open(self.file_name_out, "rb") as file_out:
            self.assertTrue(file_in.read() == file_out.read(),
                            "The input and output files should be identical.")

        # Delete the generated index file
        os.remove(self.file_name_out)

    def test_get_entry_sanity(self):
        """Modify index file - sanity check
        """
        entries = self.index_file.get_entries_by_filename("random-file.py")
        self.assertTrue(len(entries) == 0, "Random entries present in index")

        entries = self.index_file.get_entries_by_filename(self.test_files[0])
        self.assertTrue(len(entries) == 1, "git_index.py is missing from index")

    def test_small_change_sanity(self):
        """Modify index file - sanity check

        Reads an index file, makes a small change and saves it as a new index
        file. Next, verifies that the original and the new files are different.
        """
        # Change path name in one of the entries in the index file (doesn't matter _which_)
        entries = self.index_file.get_entries_by_filename(self.test_files[1])
        entries[0].path_name = "PATHNAME_MODIFIED_IN_TEST.py"
        self.index_file.validate()

        # Save the modified file
        self.index_file.print_to_file(self.file_name_out)

        # Compare the two index files
        with open(self.file_name_in, "rb") as file_in, open(self.file_name_out, "rb") as file_out:
            self.assertFalse(file_in.read() == file_out.read(),
                             "The input and output files should be different.")

        # Delete the generated index file
        os.remove(self.file_name_out)

    def test_add_file(self):
        """Test the add_file method
        """

        # A dummy file that will be added to the index
        test_file = "ADD_FILE_TEST_FILE.py"
        with open(test_file, 'w', encoding='utf-8'):

            # Verify that the dummy test file is not present in the index
            entries = self.index_file.get_entries_by_filename(test_file)
            self.assertTrue(len(entries) == 0,
                             "The test file is already present, but has not "
                             "been added yet.")

            # Add the test file to the index
            old_sha1 = self.index_file.checksum
            self.index_file.add_file(test_file)

            # Verify that the test file is present in the index
            entries = self.index_file.get_entries_by_filename(test_file)
            self.assertTrue(len(entries) == 1,
                             "The test file has already been added, but seems not to "
                             "be present.")

            # Verify that the chcecksum of the index has changed
            self.assertTrue(old_sha1 != self.index_file.checksum,
                             "The input and output files should be different.")

        # Delete the dummy test file
        os.remove(test_file)

    def test_get_trees_to_add_or_update(self):
        """Test the `get_trees_to_add_or_update` method
        """

        # Create a dummy test file that will be added to the index
        test_file = os.path.join("test-dir-2", "test-dir-3", "test-dir-4",
                "file.txt")
        Path(self.test_repo_dir, test_file).touch()

        # `get_trees_to_add_or_update` assumes that the current dir is the root
        # repo dir. Hence we need to change the directories.
        cwd = os.getcwd()
        os.chdir(self.test_repo_dir)

        self.index_file.add_file(test_file)
        # Get the data to verify
        new_dirs, dirs_to_update = self.index_file.get_trees_to_add_or_update()

        # Return to the original test dir
        os.chdir(cwd)

        # Verify the generated output
        self.assertTrue(len(new_dirs) == 1, "Incorrect number of trees to add!")
        self.assertTrue(len(dirs_to_update) == 3, "Incorrect number of trees to updated!")

        # Delete the dummy test file
        os.remove(os.path.join(self.test_repo_dir, test_file))

    def test_checksum_sanity(self):
        """Re-calculate the index checksum and verify that it is correct. The
        index is neither modified nor updated.
        """
        # Calculate SHA-1
        contents = self.index_file.print_to_bytes()
        new_sha1 = hashlib.sha1(contents).hexdigest()

        # Verify that the checksum is correct
        self.assertTrue(self.index_file.checksum == new_sha1,
                "Checksum is invalid")

    def test_update_checksum_basic(self):
        """Re-calculate the index checksum and verify that it is correct. The
        index is not modified, but the checksum gets updated (with the index
        kept intact, this should be a nop).
        """
        old_sha1 = self.index_file.checksum

        # Update the checksum in the index file. As the index has not been
        # modified, this should not affect the checksum.
        self.index_file.update_checksum()
        self.assertTrue(self.index_file.checksum == old_sha1,
                "Checksum is invalid")

    def test_update_checksum(self):
        """Re-calculate the index checksum and verify that it is correct. The
        index is modified and the checksum is updated.

        Updating the index invalidates the checksum. Verify this and that
        IndexFile.update_checksum() correctly updates it to reflect the updated
        content.
        """
        # Change path name in one of the entries in the index file (it doesn't
        # matter _which_). Note that this invalidates the current index checksum.
        entries = self.index_file.get_entries_by_filename(self.test_files[0])
        entries[0].path_name = "PATHNAME_MODIFIED_IN_TEST.py"

        entries = self.index_file.get_entries_by_filename(self.test_files[1])
        entries[0].path_name = "PATHNAME2_MODIFIED_IN_TEST.py"

        # Calculate new SHA-1
        contents = self.index_file.print_to_bytes()
        new_sha1 = hashlib.sha1(contents).hexdigest()

        self.assertFalse(self.index_file.checksum == new_sha1,
                "Checksum not updated yet")

        # Update the checksum in the index file
        self.index_file.update_checksum()
        self.assertTrue(self.index_file.checksum == new_sha1,
                "Checksum has been succesfully updated")

    def test_file_mode(self):
        """ Verify that file entries in index have correct file mode
        """
        regular_file_mode = 0o100644
        for repo_file in self.test_files:
            file_entries = self.index_file.get_entries_by_filename(repo_file)
            self.assertTrue(file_entries[0].mode == regular_file_mode)
            # There should only be one file that matches `repo_file`. You can
            # check `create_test_repo.sh` to verify.
            self.assertTrue(len(file_entries) == 1,
                f"More than one file found matching {repo_file}!")

    def test_get_entries_by_dirname(self):
        """ Test the `get_entries_by_dirname` method
        """
        for repo_dir in self.test_dirs:
            dir_entries = self.index_file.extension_tree_cache.get_entries_by_dirname(repo_dir)
            # There should only be one dir that matches `repo_dir`. You can
            # check `create_test_repo.sh` to verify.
            self.assertTrue(len(dir_entries) == 1,
                f"More than one dir found matching {repo_dir}!")

    def test_is_dir_in_index(self):
        """ Test the `is_dir_in_index` method
        """
        for repo_dir in self.test_dirs:
            self.assertTrue(self.index_file.is_dir_in_index(repo_dir),
                f"{repo_dir} not present, but it was added to the repo!")

        self.assertFalse(self.index_file.is_dir_in_index("some_random_invalid_path"),
                "This directory is not present in the repo!")

    def test_get_blobs(self):
        """ Test the `get_blobs` method
        """

        blobs = self.index_file.get_blobs("./")
        self.assertTrue(len(blobs) == 1, "Invalid number of blobs")

        blobs = self.index_file.get_blobs("./test-dir-1")
        self.assertTrue(len(blobs) == 1, "Invalid number of blobs")

        blobs = self.index_file.get_blobs("./test-dir-2")
        self.assertTrue(len(blobs) == 0, "Invalid number of blobs")

        blobs = self.index_file.get_blobs("./test-dir-2/test-dir-3")
        self.assertTrue(len(blobs) == 3, "Invalid number of blobs")

    def test_get_subtrees(self):
        """ Test the `get_subtrees` method
        """

        subtrees = self.index_file.get_subtrees("./")
        self.assertTrue(len(subtrees) == 2, "Invalid number of subtrees")

        subtrees = self.index_file.get_subtrees("test-dir-1")
        self.assertTrue(len(subtrees) == 0, "Invalid number of subtrees")

        subtrees = self.index_file.get_subtrees("test-dir-2")
        self.assertTrue(len(subtrees) == 1, "Invalid number of subtrees")

        subtrees = self.index_file.get_subtrees("test-dir-3")
        self.assertTrue(len(subtrees) == 0, "Invalid number of subtrees")

    def test_tree_cache_extension_invalidate(self):
        """ Test the `invalidate` and `validate` methods

        The invalidate() member method in IndexTreeCacheExt will invalidate
        an entry in the tree cache, but it shouldn't invalidate the underlying
        object (i.e. the object should still represent a valid Git extension
        with one field marked as invalidated). Verify that.
        """
        self.index_file.extension_tree_cache.validate()
        self.index_file.validate()

        self.index_file.extension_tree_cache.invalidate("NOT_A_VALID_PATH")
        self.index_file.extension_tree_cache.validate()
        self.index_file.validate()

        self.index_file.extension_tree_cache.invalidate(".")
        self.index_file.extension_tree_cache.validate()
        self.index_file.validate()
        self.index_file.validate()

    def test_tree_cache_extension_add_entry_valid(self):
        """ Test the `add_entry` member method when used correctly

        New tries are inserted in the correct, top-down order.
        """
        new_tree_1 = git_index.IndexTreeEntry("./test_dir", 0, 0, "abcdef")
        self.index_file.extension_tree_cache.add_entry(new_tree_1)
        new_tree_2 = git_index.IndexTreeEntry("./test_dir/test_dir_2", 0, 0,
                "123456")
        self.index_file.extension_tree_cache.add_entry(new_tree_2)

        self.index_file.extension_tree_cache.validate()

    def test_tree_cache_extension_add_entry_invalid_1(self):
        """ Test the `add_entry` member when used incorrectly

        New tries are inserted in the incorrect, bottom-up order.
        """
        # Inserting ./test_dir/test_dir_2 before ./test_dir is insert is
        # invalid.
        new_tree = git_index.IndexTreeEntry("./test_dir/test_dir_2",
                git_index.GIT_INVALID_ENTRY_COUNT, 0, None)
        self.assertRaises(git_index.GFGError,
                self.index_file.extension_tree_cache.add_entry, new_tree)

    def test_tree_cache_extension_add_entry_invalid_2(self):
        """ Test the `add_entry` member when used incorrectly

        Inserting an entry corresponding to the top Git directory, '', is not
        allowed (it should always be there and not require inserting)
        """
        new_tree = git_index.IndexTreeEntry("./",
                git_index.GIT_INVALID_ENTRY_COUNT, 0, None)
        self.assertRaises(git_index.GFGError,
                self.index_file.extension_tree_cache.add_entry, new_tree)


if __name__ == "__main__":
    unittest.main()
