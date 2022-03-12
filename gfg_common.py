''' A collection of shared functionality
'''

import sys
import os
from pathlib import Path
import re

GIT_CHECKSUM_SIZE_BYTES = 20
# See https://git-scm.com/docs/index-format#_cache_tree
GIT_INVALID_ENTRY_COUNT = -1
# Number of ASCII characters in GIT_INVALID_ENTRY_COUNT
GIT_NUM_OF_ASCII_CHARS_INVALID_EC = 2

class GFGError(Exception):
    """ Just a small convienience class representing an exception in GFG """

def get_name_and_email(repo_dir = None):
    """ Extract the committer name and e-mail

    This method will check .git/config if repo_dir is not None. Otherwise, it
    reads $HOME/.gitconfig.

    INPUT:
        repo_dir - Git object hash to get the path for
    RETURN:
        A tuple containing the committer name and e-mail
    """
    name = None
    email = None

    # Get file path to read
    gitconfig_file_path = Path()
    if repo_dir is not None:
        gitconfig_file_path = Path(repo_dir) / ".git" / "config"
    else:
        gitconfig_file_path = Path.home() / ".gitconfig"

    assert os.path.exists(gitconfig_file_path), "FAIL"

    # Read the config file and extract the name and the e-mail
    with open(gitconfig_file_path, "r", encoding = 'utf-8') as gitconfig_file:
        regex_name = re.compile(r'^\s*name =')
        regex_email = re.compile(r'^\s*email =')
        for file_line in gitconfig_file:
            if re.match(regex_name, file_line):
                name = file_line.split('=')[1].lstrip().rstrip()
            if re.match(regex_email, file_line):
                email = file_line.split('=')[1].lstrip().rstrip()

    # If reading the local config inside the current repo, make sure that that
    # the committer name and email were actually there. If not, read the global
    # Git config.
    if repo_dir is not None:
        if name is None or email is None:
            name, email = get_name_and_email()

    return name, email

if __name__ == "__main__":
    sys.exit(1)
