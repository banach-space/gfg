''' A collection of shared functionality
'''

import sys

GIT_CHECKSUM_SIZE_BYTES = 20
# See https://git-scm.com/docs/index-format#_cache_tree
GIT_INVALID_ENTRY_COUNT = -1
# Number of ASCII characters in GIT_INVALID_ENTRY_COUNT
GIT_NUM_OF_ASCII_CHARS_INVALID_EC = 2

class GFGError(Exception):
    """ Just a small convienience class representing an exception in GFG """

if __name__ == "__main__":
    sys.exit(1)
