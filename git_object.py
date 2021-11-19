#!/usr/bin/env python3
'''Library for representing Git objects


[1] https://www.dulwich.io/docs/tutorial/file-format.html#the-blob
'''

import sys
import hashlib
import struct
from pathlib import Path
import zlib
import glob
from repository import GitRepository


class GitBlobObject():
    """A Git blob object

    A Git blob stored as packed, uncompressed blob data and the corresponding
    sha1 sum. A Git blob looks like this:
            `blob <content length><NUL><content>`
    `content` is the original file content. See [1] for more details.

    This class also stores the path for the corresponding blob:
        file_dir = <git-repo-root>/.git/objects/
        file_name = sha1[2:]

    In order to create a Git blob, you need to supply either object's has or
    packed blob content.
    """

    @staticmethod
    def get_packed_blob(file_to_read=None):
        """Get the file under `file_to_read` as a packed Git blob

        Generates a packed blob file for the input file. The blob looks like
        this (see [1]):
            `blob <content length><NUL><content>`

        ARGS:
            file_to_read - path for the file to read
        RETURN:
            data - packed data for the generated blob file

        """
        if file_to_read is not None:
            with open(file_to_read, "r", encoding = 'utf-8') as input_file:
                data = input_file.read()
        else:
            data=""
            for line in sys.stdin:
                data += line

        header_str = f"blob {len(data)}"
        header_fmt = f"{len(header_str)}s"
        packed_data = struct.pack(header_fmt, header_str.encode())

        packed_data += struct.pack('B', 0)
        struct_fmt = f"{len(data)}s"
        packed_data += struct.pack(struct_fmt, data.encode())

        return packed_data

    def __init__(self, repo: GitRepository, object_hash: str = None, packed_data: bytes = None):
        # Blob hash
        self.object_hash = object_hash
        # Blob data
        self.data = packed_data
        # Does this object exist?
        self.exists = True

        if self.object_hash is None:
            self.object_hash = hashlib.sha1(self.data).hexdigest()

        # Calculate the file path from the object hash
        self.file_dir = Path(repo.git_dir)  / "objects" / self.object_hash[0:2]
        self.file_path = Path(self.file_dir) /  self.object_hash[2:]

        # If the hash was provided by the user, it might have been a shortened
        # version. If that's the case, self.file_path needs to recalculated.
        list_of_matching_files = glob.glob(str(self.file_path) + "*")
        if len(list_of_matching_files) == 1:
            self.file_path = Path(list_of_matching_files[0])

        # Now that we have the blob file path, check whether this object
        # actually exists
        if not self.file_path.exists():
            self.exists = False
            return

        # If the blob data was no provided, read it from the corresponding file
        if self.data is None:
            with open(self.file_path, "rb") as input_file:
                data =  input_file.read()
                self.data = zlib.decompress(data)

    def read(self):
        """Read this blob object and print to stdout"""
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}")
            return

        # Read object type
        space_after_obj_type = self.data.find(b' ')
        # Not yet needed
        # object_type = self.data[0:space_after_obj_type]

        # Read and validate object size
        null_char_after_obj_type = self.data.find(b'\x00', space_after_obj_type)
        object_size = int(self.data[space_after_obj_type:null_char_after_obj_type].decode("ascii"))
        if object_size != len(self.data)-null_char_after_obj_type-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        print(self.data[null_char_after_obj_type+1:].decode("ascii"), end="")

    def write(self):
        """Save this blob file

        The blob file is compressed using zlib and saved to .git/objects as a
        physical file. If the file already exists, do nothing.
        """
        dir_name = self.object_hash[0:2]
        file_name = self.object_hash[2:]

        # Create the object sub-dir
        full_dir = Path("./.git/objects/" + dir_name)
        full_dir.mkdir(exist_ok=True)

        # Create the object file
        file_path = Path("./.git/objects/" + dir_name + "/" + file_name)
        try:
            file_path.touch(exist_ok=False)
        except FileExistsError:
            return

        # Save the object file
        file_path.write_bytes(zlib.compress(self.data))

    def verify(self):
        """ Trivial sanity check """
        assert self.object_hash == hashlib.sha1(self.data).hexdigest(), \
            "GFG: Git hash and the actual data don't match"
