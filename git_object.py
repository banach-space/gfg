#!/usr/bin/env python3
'''Library for representing Git objects


[1] https://www.dulwich.io/docs/tutorial/file-format.html#the-blob
[2] https://www.dulwich.io/docs/tutorial/file-format.html#the-commit
[3] https://www.dulwich.io/docs/tutorial/file-format.html#the-tree
'''

import sys
import binascii
import os
from collections import namedtuple
import hashlib
import struct
from pathlib import Path
import datetime
import zlib
from git_repository import GitRepository
from git_index import GFGError

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
    if not repo.is_object_in_repo(sha):
        return None

    _, file_path = repo.get_object_path(sha)

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

        if self.object_hash is None and self.data is None:
            self.exists = False
            return

        if self.object_hash is None:
            self.object_hash = hashlib.sha1(self.data).hexdigest()

        # If the object does not exist yet, there's nothing else to do at the
        # moment.
        # NOTE: Pack files are not supported!
        if not repo.is_object_in_repo(self.object_hash):
            self.exists = False
            return

        # Calculate the file path from the object hash
        self.file_dir, self.file_path = repo.get_object_path(self.object_hash)

        # If the blob data was not provided, read it from the corresponding file
        if self.data is None:
            with open(self.file_path, "rb") as input_file:
                data =  input_file.read()
                self.data = zlib.decompress(data)

        end_of_obj_type = self.data.find(b' ')
        self.object_type = self.data[0:end_of_obj_type].decode("ascii")

    def print_to_stdout(self, pretty_print : bool, type_only : bool):
        """ Read this object and print to stdout"""
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
        self.commit_msg.rstrip()


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

    def print_to_stdout(self, pretty_print: bool, type_only: bool):
        """ Print this object to stdout"""
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}")
            return

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

        return

    def print_log(self, disable_ascii_escape: bool = False):
        """Print this commit in a format identical to `git log`. Colors are
        generated using ASCII escape characters.

        INPUT:
            disable_ascii_escape - if `True`, ASCII escape characters are
                                   disabled
        """
        if not self.exists:
            print(f"fatal: Not a valid object name {self.object_hash}")
            return

        # 1. Print the commit hash.
        yellow_ansii_code = ''
        end_ansii_code = ''
        if not disable_ascii_escape:
            # NOTE: This formatting will only work in consoles that understand ANSI
            # escape sequences.
            yellow_ansii_code = '\033[33m'
            end_ansii_code = '\033[0m'
        print(f"{yellow_ansii_code}commit {self.object_hash}{end_ansii_code}")
        # 2. Print commit author.
        print(f"Author: {self.author.name} <{self.author.email}> ")
        # 3. Print commit date.
        commit_date = datetime.datetime.fromtimestamp(int(self.author.timestamp))
        print(f"Date:   {commit_date.ctime()} {self.author.timezone}")
        # 4. Print commit message. Add indentation (4 spaces) to match the
        # outpput from `git`. When splitting lines, skip the last item which
        # will only contain `\n` (we don't want to indent that).
        commit_msg_lines = self.commit_msg.split('\n')[:-1]
        commit_msg_lines = [ (4 * ' ') + line.lstrip() for line in
                commit_msg_lines]
        commit_msg = "\n".join(commit_msg_lines)
        print(f"{commit_msg}")


class GitTreeObject(GitObject):
    """ Represents a Git tree object"""

    def __parse(self):
        # Read the object type
        space_after_obj_type = self.data.find(b' ')
        object_type = self.data[0:space_after_obj_type].decode("ascii")
        assert object_type == "tree", "GFG: This is not a tree"

        # Read and validate object size
        null_char_after_obj_len = self.data.find(b'\x00', space_after_obj_type)
        self.object_size = int(
                self.data[space_after_obj_type:null_char_after_obj_len]\
                        .decode("ascii"))
        if self.object_size != len(self.data)-null_char_after_obj_len-1:
            raise Exception(f"Malformed object {self.object_hash}: bad length")

        # Read all the obhe
        idx = null_char_after_obj_len + 1
        bytes_read = 0
        while bytes_read < self.object_size:
            # Read file mode
            space_after_file_mode_idx = self.data.find(b' ', idx)
            file_mode = self.data[idx : space_after_file_mode_idx].decode("ascii").rjust(6, "0")

            # Read file name
            null_char_after_file_name = self.data.find(b'\x00', idx)
            file_name = self.data[
                    space_after_file_mode_idx:null_char_after_file_name
                    ].decode("ascii")

            # Read object hash
            idx_new = null_char_after_file_name + 21
            obj_sha = self.data[null_char_after_file_name + 1 : idx_new]

            # Get object type. Note that this is not stored in the tree object
            # and needs to be retrieved by reading the correspondig Git object.
            git_obj = GitObject(self.repo, object_hash = obj_sha.hex())
            self.tree_entries.append((file_mode, git_obj.object_type, obj_sha.hex(), file_name))

            bytes_read += (idx_new - idx)
            idx = idx_new

    def save_to_file(self):
        """ Save this tree object to an actual file """

        dir_name = self.object_hash[0:2]
        file_name = self.object_hash[2:]

        # Create the object sub-dir
        full_dir = Path("./.git/objects/" + dir_name)
        full_dir.mkdir(exist_ok=True)

        # Create the object file
        file_path = Path("./.git/objects/" + dir_name + "/" + file_name)
        if os.path.exists(file_path):
            raise GFGError(f"GFG! This tree already exists: {self.object_hash}!")

        # Save the object file
        file_path.write_bytes(zlib.compress(self.print_to_bytes()))

    def print_to_bytes(self):
        """ Print this object to a bytes object as per the spec [3] """
        tree_str = "tree"
        data: bytes = tree_str.encode()
        data += b' '
        contents = bytes()
        contents += b'\x00'

        for entry in self.tree_entries:
            # File mode. Git seems to use the value in Octoal saved using ASCII
            # chars.
            contents += str(oct(entry[0])[2:]).encode()
            contents += b' '
            # File name
            contents += os.path.basename(entry[3]).encode()
            # Null character
            contents += b'\x00'
            # Object SHA
            contents += binascii.unhexlify(entry[2].encode())
        data += str(len(contents) - 1).encode()
        data += contents

        return data

    def __init__(self, repo: GitRepository, object_hash: str = None, blobs: list
            = None, trees: list = None):
        super().__init__(repo, object_hash)

        self.object_size = 0
        self.tree_entries = []

        # If this tree already exists, just read it
        if self.exists:
            self.__parse()
            return

        if blobs is None and trees is None:
            raise GFGError("GFG: Missing data to create this object")

        for tree in trees:
            self.tree_entries.append((0o040000, "tree", tree.sha,
                tree.path_component))

        for blob in blobs:
            self.tree_entries.append((blob.mode, "blob", blob.sha1,
                blob.path_name))

        self.object_hash = hashlib.sha1(self.print_to_bytes()).hexdigest()

    def print_to_stdout(self, pretty_print : bool, type_only : bool):
        """Print this object to stdout"""
        # `gfg -t`
        if type_only:
            print("tree")
            return

        if not pretty_print:
            print(self.data)
            return

        for entry in self.tree_entries:
            # NOTE: It would be nice to give some meaningful names to these
            # fields
            print(f"{entry[0]} {entry[1]} {entry[2]}    {entry[3]} ")


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

    def print_to_stdout(self, pretty_print : bool, type_only : bool):
        """ Read this blob object and print it to stdout"""
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
