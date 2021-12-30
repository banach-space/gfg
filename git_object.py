#!/usr/bin/env python3
'''Library for representing Git objects


[1] https://www.dulwich.io/docs/tutorial/file-format.html#the-blob
[2] https://www.dulwich.io/docs/tutorial/file-format.html#the-commit
'''

import sys
from collections import namedtuple
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
        return GitTreeObject(repo, sha)

    if object_type == "blob":
        return GitBlobObject(repo, sha)

    if object_type == "commit":
        return GitCommitObject(repo, sha)

    assert False, "GFG: Unsupported object type"

class GitObject():
    """ Represents an abstract Git object"""
    sha_len = 40

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
        # pylint: disable=unused-argument
        assert self.object_type not in ["blob", "tree", "commit"], \
                "GFG: Wrong `print` version"
        raise Exception("Unimplemented!")

    def verify(self):
        """ Trivial sanity check """
        assert self.object_hash == hashlib.sha1(self.data).hexdigest(), \
            "GFG: Git hash and the actual data don't match"

class GitCommitObject(GitObject):
    """ Represents a Git commit object"""
    Author = namedtuple('Author', 'name email timestamp timezone')
    Committer = namedtuple('Committer', 'name email timestamp timezone')

    def __init__(self, repo: GitRepository, object_hash: str = None, packed_data: bytes = None):
        super().__init__(repo, object_hash, packed_data)
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}")
            return

        self.parent_sha = None
        self.tree_sha = None
        self.committer = None
        self.author = None
        self.commit_msg = None

        # Read the object type
        space_after_obj_type = self.data.find(b' ')
        self.object_type = self.data[0:space_after_obj_type].decode("ascii")
        assert self.object_type == "commit", "GFG: This is not a commit"

        # Read and validate the object size
        null_char_after_obj_len = self.data.find(b'\x00', space_after_obj_type)
        self.object_size = int(
                self.data[space_after_obj_type:null_char_after_obj_len].decode("ascii")
                )
        if self.object_size != len(self.data)-null_char_after_obj_len-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        # Read: parent, author, committer, tree
        idx = null_char_after_obj_len + 1
        while True:
            space_after_field_id = self.data.find(b' ', idx)

            field_id = str(self.data[idx:space_after_field_id].decode("ascii"))

            if field_id == "parent":
                self.parent_sha = str(
                        self.data[space_after_field_id + 1:\
                                space_after_field_id + 1 + GitObject.sha_len].
                        decode("ascii"))

            if field_id == "author":
                author = GitCommitObject.parse_author_or_committer(
                                self.data,
                                space_after_field_id + 1)
                self.author = GitCommitObject.Author(*author)
            if field_id == "committer":
                committer = GitCommitObject.parse_author_or_committer(
                                self.data,
                                space_after_field_id + 1)
                self.committer = GitCommitObject.Committer(*committer)
            if field_id == "tree":
                self.tree_sha = str(
                        self.data[space_after_field_id + 1:\
                                space_after_field_id + 1 + GitObject.sha_len].
                        decode("ascii"))

            idx = self.data.find(b'\n', idx)
            idx += 1
            # Is the next line empty? If yes, then what follows is the commit
            # message
            if self.data[idx:idx+1] == b'\n':
                break

        # Read the commit message
        self.commit_msg = str(self.data[idx:].decode("ascii"))


    @staticmethod
    def parse_author_or_committer(data, begin_idx):
        """Parses the author or committer entry in a commit object [2]. Both
        entries are similar and look like this:
            (...)
            committer|author <author name> <author e-mail> <timestamp> <timezone>
            ^
            |
            |
        begin_idx

        INPUT:
            data - raw data to read (from a Git commit object)
            begin_idx - specifies where to begin reading within `data` (as
                        highlighted above)
        RETURN:
            A tuple that contains name, email, timestamp and timezone
        """
        email_start_idx = data.find(b'<', begin_idx) + 1
        email_end_idx = data.find(b'>', email_start_idx)
        timestamp_start_idx = data.find(b' ', email_end_idx) + 1
        timezone_start_idx = data.find(b' ', timestamp_start_idx) + 1
        timezone_end_idx = data.find(b'\n', timezone_start_idx)

        name = str(data[begin_idx:email_start_idx - 2].decode("ascii"))
        email = str(data[email_start_idx:email_end_idx].decode("ascii"))
        timestamp = str(data[timestamp_start_idx:timezone_start_idx-1].decode("ascii"))
        timezone = str(data[timezone_start_idx:timezone_end_idx].decode("ascii"))

        return name, email, timestamp, timezone

    def print(self, pretty_print : bool, type_only : bool):
        """Print this object to stdout"""
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}")
            return

        # Read object type
        space_after_obj_type = self.data.find(b' ')
        object_type = self.data[0:space_after_obj_type].decode("ascii")
        assert object_type == "commit", \
            "GFG: This is not a commit"
        # `gfg -t`
        if type_only:
            print("commit")
            return

        if not pretty_print:
            print(self.data)
            return

        print(f"tree {self.tree_sha}")
        if self.parent_sha is not None:
            print(f"parent {self.parent_sha}")
        print(f"author {self.author.name} <{self.author.email}> "\
                f"{self.author.timestamp} {self.author.timezone}")
        print(f"committer {self.committer.name} "\
                f"<{self.committer.email}> {self.committer.timestamp} "\
                f"{self.committer.timezone}")
        # The commit message will contain `\n` (that's how it's read by GFG), so
        # we need to make sure not to add an additional EOL character here.
        print(self.commit_msg, end='')


class GitTreeObject(GitObject):
    """ Represents a Git tree object"""

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
        null_char_after_obj_len = self.data.find(b'\x00', space_after_obj_type)
        object_size = int(self.data[space_after_obj_type:null_char_after_obj_len].decode("ascii"))
        if object_size != len(self.data)-null_char_after_obj_len-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        idx = null_char_after_obj_len + 1
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
        null_char_after_obj_len = self.data.find(b'\x00', space_after_obj_type)
        object_size = int(self.data[space_after_obj_type:null_char_after_obj_len].decode("ascii"))
        if object_size != len(self.data)-null_char_after_obj_len-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        # Print the contents
        print(self.data[null_char_after_obj_len+1:].decode("ascii"), end="")

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
