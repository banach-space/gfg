#!/usr/bin/env python3
'''Library for representing Git objects


[1] https://www.dulwich.io/docs/tutorial/file-format.html#the-blob
'''

import sys
import hashlib
import struct
from pathlib import Path
import zlib
from git_repository import GitRepository

def create_git_object(repo : GitRepository, sha):
    """ Create a GitObject

    Creates an instance of GitObject for the Git object correspondong to `sha`
    and which is part of `repo`.

    INPUT:
        repo - Git repository to which the object belongs
        sha - Git object sha
    RETURN:
        The generated object or None
    """
    _, file_path = repo.get_object_path(sha)
    if not file_path.exists():
        return None

    # If the blob data was not provided, read it from the corresponding file
    data = bytes()
    with open(file_path, "rb") as input_file:
        data =  zlib.decompress(input_file.read())

    end_of_obj_type = data.find(b' ')
    object_type = data[0:end_of_obj_type].decode("ascii")

    if object_type == "tree":
        return GitObject(repo, sha)

    if object_type == "blob":
        return GitBlobObject(repo, sha)

    assert False, "GFG: Unsupported object type"

class GitObject():
    """ Represents a Git object"""
    def __init__(self, repo: GitRepository, object_hash: str = None, packed_data: bytes = None):
        self.repo = repo
        # The hash of this object
        self.object_hash = object_hash
        # Blob data
        self.data = packed_data
        # The type of this object (tree, blob, commit)
        self.object_type = None
        # Does this object already exist as a Git object?
        self.exists = True

        if self.object_hash is None:
            self.object_hash = hashlib.sha1(self.data).hexdigest()

        # Calculate the file path from the object hash
        self.file_dir, self.file_path = repo.get_object_path(self.object_hash)

        # Now that we have the blob file path, check whether this object
        # actually exists
        # NOTE: Pack files are not supported!
        if not self.file_path.exists():
            self.exists = False
            return

        # If the blob data was not provided, read it from the corresponding file
        if self.data is None:
            with open(self.file_path, "rb") as input_file:
                data =  input_file.read()
                self.data = zlib.decompress(data)

        end_of_obj_type = self.data.find(b' ')
        self.object_type = self.data[0:end_of_obj_type].decode("ascii")

    def print(self, pretty_print : bool, type_only : bool):
        """Read this object and print to stdout"""
        # pylint: disable=R0914
        # (don't warn about "Too many local variables")
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}")
            return

        # Read object type
        space_after_obj_type = self.data.find(b' ')
        object_type = self.data[0:space_after_obj_type].decode("ascii")
        assert object_type == "tree", \
            "GFG: This is not a tree"
        # `gfg -t`
        if type_only:
            print("tree")
            return

        if not pretty_print:
            print(self.data)
            return

        # Read and validate object size
        null_char_after_obj_type = self.data.find(b'\x00', space_after_obj_type)
        object_size = int(self.data[space_after_obj_type:null_char_after_obj_type].decode("ascii"))
        if object_size != len(self.data)-null_char_after_obj_type-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        idx = null_char_after_obj_type + 1
        bytes_read = 0
        while bytes_read < object_size:
            null_char_after_file_name = self.data.find(b'\x00', idx)
            next_idx = self.data.find(b' ', idx)
            file_mode = self.data[idx : next_idx].decode("ascii").rjust(6, "0")
            file_name = self.data[next_idx: null_char_after_file_name].decode("ascii")

            idx_new = null_char_after_file_name + 21
            file_sha = self.data[null_char_after_file_name + 1 : idx_new]
            git_obj = GitObject(self.repo, object_hash = file_sha.hex())
            print(f"{file_mode} {git_obj.object_type} {file_sha.hex()}    {file_name} ")
            bytes_read += (idx_new - idx)
            idx = idx_new

    def verify(self):
        """ Trivial sanity check """
        assert self.object_hash == hashlib.sha1(self.data).hexdigest(), \
            "GFG: Git hash and the actual data don't match"


class GitBlobObject(GitObject):
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
            # pylint: disable=R1713
            # Pylint suggests using `data.join(sys.stdin)` here instead of the
            # `for` loop, but that doesn't work. AFAIK, `sys.stdin` is an
            # iterable so it should actually work. For now I'm just disabling
            # the Pylint warning for this block.
            data=str()
            for line in sys.stdin:
                data += line

        header_str = f"blob {len(data)}"
        header_fmt = f"{len(header_str)}s"
        packed_data = struct.pack(header_fmt, header_str.encode())

        packed_data += struct.pack('B', 0)
        struct_fmt = f"{len(data)}s"
        packed_data += struct.pack(struct_fmt, data.encode())

        return packed_data

    def print(self, pretty_print : bool, type_only : bool):
        """Read this blob object and print it to stdout"""
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}", file=sys.stderr)
            return

        # Read object type
        space_after_obj_type = self.data.find(b' ')
        object_type = self.data[0:space_after_obj_type].decode("ascii")
        assert object_type == "blob", \
            "GFG: This is not a object"
        if type_only:
            print("blob")
            return

        # Read and validate object size
        null_char_after_obj_type = self.data.find(b'\x00', space_after_obj_type)
        object_size = int(self.data[space_after_obj_type:null_char_after_obj_type].decode("ascii"))
        if object_size != len(self.data)-null_char_after_obj_type-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        # Print the contents
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
