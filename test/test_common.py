# test_common.py
"""Unit tests for the gfg_common module

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
import gfg_common

class TestGitRepositoryClass(unittest.TestCase):
    """Top unit test class for this module
    """

    def setUp(self):
        # Create a test repo
        with subprocess.Popen(["bash", "create_test_repo.sh", "."],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
            self.test_repo_dir = Path(process.stdout.read().decode().strip('\n'))

    def tearDown(self):
        # Remove the test repo
        rmtree(self.test_repo_dir)

    def test_get_name_and_email(self):
        """ Test the get_name_and_email method """
        name, email = gfg_common.get_name_and_email(self.test_repo_dir)

        # Values extracted from create_test_repo.sh
        self.assertTrue(name, "GFG Test")
        self.assertTrue(email, "gfg@gfg.test")

if __name__ == "__main__":
    unittest.main()
