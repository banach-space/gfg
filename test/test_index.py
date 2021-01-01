# test_index.py
"""Unit tests for index-file related classes

"""

from shutil import copyfile
import os
import unittest
import index


class TestIndexClass(unittest.TestCase):
    """Top unit test class for this module

    """
    file_name_in = "index_test_in"
    file_name_out = "index_test_out"
    index_file = None

    def setUp(self):
        index_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../.git/index")
        copyfile(index_path, self.file_name_in)
        self.index_file = index.IndexFile(self.file_name_in)
        self.index_file.parse()

    def tearDown(self):
        os.remove(self.file_name_out)
        os.remove(self.file_name_in)

    def test_read_write_sanity(self):
        """Read-write - sanity check

        Simply reads an index file, saves a fresh copy of it and then verifies
        that both files (original and saved) are identica.
        """
        # Simply save the input index file into the output file
        self.index_file.print_to_file(self.file_name_out)

        # Compare the two index files
        file_in = open(self.file_name_in, "rb")
        file_out = open(self.file_name_out, "rb")
        self.assertTrue(file_in.read() == file_out.read(),
                        "The input and output files should be identical.")

        # Close the index files
        file_in.close()
        file_out.close()

    def test_small_change_sanity(self):
        """Modify index file - sanity check

        Reads an index file, makes a small change and saves it as a new index
        file. Next, verifies that the original and the new files are different.
        """
        # Change path name in one of the entries in the index file (doesn't matter _which_)
        entries = self.index_file.get_entries_by_filename("index.py")
        entries[0].path_name = "corrupted.py"
        self.index_file.validate()

        # Save the modified file
        self.index_file.print_to_file(self.file_name_out)

        # Compare the two index files
        file_in = open(self.file_name_in, "rb")
        file_out = open(self.file_name_out, "rb")
        self.assertFalse(file_in.read() == file_out.read(),
                         "The input and output files should be different.")

        # Close the index files
        file_in.close()
        file_out.close()


if __name__ == "__main__":
    unittest.main()
