#!/usr/bin/env python3
'''Library for representing Git objects'''

import hashlib
import struct
from pathlib import Path
import zlib

class GitObject():
    """A Git object

    This is a very basic PoC and requires more work
    """

    def __init__(self, file_path):
        with open(file_path, "r", encoding = 'utf-8') as input_file:
            self.data =  input_file.read()

        header_str = f"blob {len(self.data)}"
        header_fmt = f"{len(header_str)}s"
        self.contents = struct.pack(header_fmt, header_str.encode())

        self.contents += struct.pack('B', 0)
        struct_fmt = f"{len(self.data)}s"
        self.contents += struct.pack(struct_fmt, self.data.encode())

        self.hash = hashlib.sha1(self.contents).hexdigest()

    def write(self):
        """TODO"""
        dir_name = self.hash[0:2]
        file_name = self.hash[2:]

        full_dir = Path("./.git/objects/" + dir_name)
        full_dir.mkdir()
        file_path = Path("./.git/objects/" + dir_name + "/" + file_name)
        file_path.touch()

        struct_fmt = f"{len(self.data)}s"
        file_path.write_bytes(zlib.compress(self.contents))
