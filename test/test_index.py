# test_index.py
"""Unit tests for index-file related classes

Note that it uses the index file from the GFG repository as test input. This
allows us to make some assumptions about the contents of the index file. It
also means that test input is getting more and more complex. This is good for
code coverage, but will hurt reproducibility.
"""

from shutil import copyfile
import os
import unittest
import hashlib
import git_index


class TestIndexClass(unittest.TestCase):
    """Top unit test class for this module

    """
    file_name_in = "index_test_in"
    file_name_out = "index_test_out"
    index_file = None

    def setUp(self):
        # Copy the index file of GFG and use that as input for tests
        index_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.git/index")
        copyfile(index_path, self.file_name_in)
        self.index_file = git_index.IndexFile(self.file_name_in)

        # Parse the index file and validate it
        self.index_file.validate()

    def tearDown(self):
        os.remove(self.file_name_in)

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

        entries = self.index_file.get_entries_by_filename("git_index.py")
        self.assertTrue(len(entries) == 1, "git_index.py is missing from index")

    def test_small_change_sanity(self):
        """Modify index file - sanity check

        Reads an index file, makes a small change and saves it as a new index
        file. Next, verifies that the original and the new files are different.
        """
        # Change path name in one of the entries in the index file (doesn't matter _which_)
        entries = self.index_file.get_entries_by_filename("git_index.py")
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

    def test_update_checksum_sanity(self):
        """Checksum - sanity check

        Verify that the index checksum is correct
        """
        # Calculate SHA-1
        contents = self.index_file.print_to_bytes()
        new_sha1 = hashlib.sha1(contents).hexdigest()

        self.assertTrue(self.index_file.checksum == new_sha1,
                "Checksum is invalid")

        # Try updating the checksum in the index file (as we have not modified
        # the index, this shouldn't really change the checksum)
        self.index_file.update_checksum()
        self.assertTrue(self.index_file.checksum == new_sha1,
                "Checksum is invalid")

    def test_update_checksum(self):
        """Modify the checksum

        Updating the index invalidates the checksum. Verify this and that
        IndexFile.update_checksum() correctly updates it to reflect the updated
        content.
        """
        # Change path name in one of the entries in the index file (it doesn't
        # matter _which_). Note that this invalidates the current index checksum.
        entries = self.index_file.get_entries_by_filename("git_index.py")
        entries[0].path_name = "PATHNAME_MODIFIED_IN_TEST.py"

        entries = self.index_file.get_entries_by_filename("git_repository.py")
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


if __name__ == "__main__":
    unittest.main()
