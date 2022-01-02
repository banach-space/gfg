# vindex.py
'''Library for representing, reading and editing Git index files.

This library implements classes represent Git index files. The provided methods
will all you to easily read/parse and modify/write index files. See [1|4] for
reference documentation.

Limitations:
    * only versions up to 3 (inclusive) are supported
    * although extensions are preserved, they are not parsed
    * only SHA-1 repositories are supported
    * path names longer than 2048 (OxFFF) are not supported

[1] Git index format:
    https://github.com/git/git/blob/master/Documentation/technical/index-format.txt
[2] Struct Format Characters:
    https://docs.python.org/3/library/struct.html#format-characters
[3] Struct Format Strings:
    https://docs.python.org/3/library/struct.html#format-strings
[4] Git index format:
    https://git-scm.com/docs/index-format
[5] Git Tree Cache Extension
    https://docs.microsoft.com/en-us/archive/msdn-magazine/2017/august/devops-git-internals-architecture-and-index-files#index-extensions
'''

import binascii
import mmap
import struct
import os
import sys
import hashlib
from pathlib import Path

from pprint import pprint

GIT_CHECKSUM_SIZE_BYTES = 20
# See https://git-scm.com/docs/index-format#_cache_tree
GIT_INVALID_ENTRY_COUNT = -1
# Number of ASCII characters in GIT_INVALID_ENTRY_COUNT
GIT_NUM_OF_ASCII_CHARS_INVALID_EC = 2


def read_from_mmapped_file(mmaped_file, format_char):
    """Reads an integer from a memory mapped file

    Reads, unpacks and returns an integer from a memory mapped file. The size
    of the integer to read is specified via a format char (documented in [2]).
    As per `Git index format` [1|4], all binary numbers are in network byte
    order. As documented in [3], this translates to `!` in the format string.

    Args:
        mmaped_file - the memory mapped file to read from
        format_char - use this to specify the size of the integer to read (see
            [2] for reference)
    Returns:
        the integer that was read
    """
    data_format = "! " + format_char
    num_bytes = mmaped_file.read(struct.calcsize(data_format))
    return struct.unpack(data_format, num_bytes)[0]


def write_to_mmapped_file(mmaped_file, data, format_char):
    """Writes an integer into a memory mapped file

    Packs and writes an integer into a memory mapped file. The size of the
    integer to write is specified via a format char (documented in [2]).  As
    per `Git index format` [1|4], all binary numbers are in network byte order.
    As documented in [3], this translates to `!` in the format string.

    Args:
        mmaped_file - the memory mapped file to write to
        data - integer to write
        format_char - use this to specify the size of the integer to write (see
            [2] for reference)
    """
    data_format = "! " + format_char
    data_packed = struct.pack(data_format, data)
    num_bytes = mmaped_file.write(data_packed)
    assert len(data_packed) == num_bytes, "Error"


class IndexFile():
    """Represents one physical `Git index format` [1|4] file

    This class encapsulates a `Git index format` [1|4] file. Use it to read,
    parse, modify and save such files. It follows the official specification -
    any divergences are either annotated or guarded with exceptions. Any
    attempt to read or write a file in a format that's not supported will raise
    an exceptions. These are documented in the respective methods. See also the
    list of limitations documented in the module docstring.
    """

    def __init__(self, filename):
        self.index_file_name = filename
        self.header = IndexHeader()
        self.extension_tree_cache = IndexTreeCacheExt()

        # A list of index entries. Every item is a tuple: (idx, entry)
        self.entries = []

        # Extensions as plain bytes
        self.extensions = b''

        self.checksum = str("")

        # If there's an index file in this repo already - parse it.
        # Repositories that have just been initialised won't contain an index
        # file yet.
        index_file = Path(self.index_file_name)
        if index_file.exists():
            self.__parse()

    def update_checksum(self):
        """Updates the checksum based on the current contents

        The checksum should always reflect the current contents of the index
        file. Use this method after updating the contents of the index file.
        """
        self.checksum = ""
        contents = self.print_to_bytes()
        self.checksum = hashlib.sha1(contents).hexdigest()

    def validate(self):
        """Validate the contents stored by this IndexFile
        """
        assert len(self.entries) == self.header.num_entries, \
            "GFG: The index header and actual " \
            "contents are inconsistent."

        with open(self.index_file_name, "rb") as index_file:
            index_content = index_file.read()[:-20]
            assert self.checksum == hashlib.sha1(index_content).hexdigest(), \
                    "GFG: Index file checksum is invalid"

        self.extension_tree_cache.validate()

    def __parse(self):
        """Parse the index file

        Parses the contents of the index file corresponding to this instance of
        IndexFile. Member fields are set accordingly.

        Limitations:
            * Only the tree cache extension is currently supported
        """
        with open(self.index_file_name, "rb") as index_file_obj:
            index_file = mmap.mmap(
                index_file_obj.fileno(), 0, prot=mmap.PROT_READ)

            # Parse header
            self.header = IndexHeader()
            self.header.read(index_file)

            # Parse index entries
            for entry_idx in range(self.header.num_entries):
                entry = IndexEntry()
                entry.read(index_file, self.header.ver_num)
                self.entries.append((entry_idx, entry))

            # Parse extensions (for now we just read the bytes)
            index_len = index_file.size()
            num_bytes_remaining = (
                index_len - GIT_CHECKSUM_SIZE_BYTES) - index_file.tell()
            self.extensions = index_file.read(num_bytes_remaining)
            self.extension_tree_cache = IndexTreeCacheExt(self.extensions)

            # Parse checksum
            self.checksum = binascii.hexlify(
                index_file.read(GIT_CHECKSUM_SIZE_BYTES)).decode("ascii")

            index_file.close()

        self.validate()

    def print_to_file(self, output_file=None, with_checksum=True):
        """Prints the contents of this class into a physical file

        Goes over all fields stored in the self object and prints them into output_file as binary
        data (i.e. according to the spec [1|4]).

        Args:
            * output_file - the name of the output index file (defaults to self.index_file_name,
            i.e. the original file is overwritten with potentially updated data)
        """
        if output_file is None:
            output_file = self.index_file_name

        with open(output_file, "wb") as index_file:
            index_file.write(self.print_to_bytes())

            if with_checksum:
                index_file.write(binascii.unhexlify(self.checksum.encode()))

    def print_to_bytes(self):
        """Pack this IndexFile as a bytes object"""
        # Pack the header
        contents = self.header.print_to_bytes()

        # Pack the entries
        for _, entry in self.entries:
            contents += entry.print_to_bytes(self.header.ver_num)

        # Pack the extensions
        # NOTE: Add support for more extensions. Currently only tree cache is
        # supported.
        contents += self.extension_tree_cache.print_to_bytes()

        return contents

    def print_to_stdout(self):
        """Prints the contents of this class into stdout

        Goes over all fields stored in the self object and prints them into stdout in textual form.
        """
        pprint(self.header.__dict__)

        print(f"len(self.entries): {len(self.entries)}")
        for entry in self.entries:
            print("[entry]")
            pprint(entry[1].__dict__)

        print("[extensions]")
        pprint(self.extension_tree_cache.__dict__)
        print("[checksum]")
        pprint(self.checksum)

    def get_entries_by_filename(self, file_to_retrieve):
        """Retrieve index entries corresponding to the specified file

        Retrieves the list of index entries that correspond to file_to_retrieve.  Note that there
        might be more than one such entry, e.g. when there are multiple files with similar names,
        but in different subdirectories. Currently, in such cases an exception is raised.

        TODO: Add support for repositories in which similarly named files are stored in multiple
        subdirectories.

        Args:
            file_to_retrieve - name of the file for which the index entries are requested
        Returns:
            A list of matching index entries
        """
        _, file_name = os.path.split(file_to_retrieve)
        matching_entries = [entry for _, entry in self.entries
                            if os.path.split(entry.path_name)[1] == file_name]

        if matching_entries != [] and not len(matching_entries) == 1:
            raise Exception(
                "GFG: More than one path matches the query. Resolution not yet support")

        return matching_entries

    def add_file(self, path):
        """Add a new file to this index file"""
        self.entries.append((len(self.entries) + 1, (IndexEntry(path))))
        self.header.num_entries += 1
        self.extension_tree_cache.invalidate(os.path.dirname(path))

        self.update_checksum()
        self.print_to_file()
        self.validate()

class IndexHeader():
    """Represents a Git index header
    """
    # 4-byte signature, b"DIRC"
    signature = None
    # 4-byte version number
    ver_num = None
    # 32-bit number of index entries, i.e. 4-byte
    num_entries = None

    def __init__(self):
        self.signature = "DIRC"
        self.ver_num = 2
        self.num_entries = 0

    def write(self, index_file):
        """Save this header to a file

        Saves this header to a memory mapped Git index file. The header is assumed to
        be formatted as specified by the docs [1|4].

        Args:
            index_file - memory mapped Git index file to write to
        """
        index_file.write(self.print_to_bytes())

    def print_to_bytes(self):
        """Pack this header a bytes object
        """
        contents = self.signature.encode()

        data_format = "! " + "I"
        contents = contents + struct.pack(data_format, self.ver_num)
        contents = contents + struct.pack(data_format, self.num_entries)

        return contents

    def read(self, index_file):
        """Read Git index header from a file

        Reads header from the input memory mapped Git index file. The header is assumed to
        be formatted as specified by the docs [1|4]. The data is saved in `self`.

        Args:
            index_file - memory mapped Git index file to read from
        """
        self.signature = index_file.read(4).decode("ascii")
        assert self.signature == "DIRC", "Not a Git index file"

        self.ver_num = read_from_mmapped_file(index_file, "I")
        assert self.ver_num in {2, 3}, f"Unsupported version: {self.ver_num}"

        self.num_entries = read_from_mmapped_file(index_file, "I")


class IndexEntry():
    """Represents a Git index entry
    """
    # pylint: disable=too-many-instance-attributes

    # The last time a file's metadata changed
    ctime_s = None
    ctime_ns = None

    # The last time a file's data changed
    mtime_s = None
    mtime_ns = None

    # The ID of device containing this file
    dev = None

    # The file's inode number
    ino = None

    # 32-bit mode, split into (high to low bits)
    mode = None

    # stat(2) data
    uid = None
    gid = None
    size = None

    # Object name (SHA-1 ID) for the represented object. We are using
    # SHA-1, which are 160 bits wide. That's 20 bytes.
    sha1 = None

    # A 16-bit 'flags' field split into:
    assume_valid = 0
    extended = 0
    stage = (0, 0)
    name_len = 0

    # (Version 3 or later) A 16-bit field, only applicable if the
    # "extended flag" above is 1, split into:
    # 1-bit reserved for future
    reserved = None
    # 1-bit skip-worktree flag (used for sparse checkout)
    skip_worktree = None
    # 1-bit intent-to-add flag (used by "git add -N")
    intent_to_add = None
    # 13-bits unused, must be zero
    unused = None

    # Entry path name (variable length) relative to top level directory
    # (without leading slash).
    path_name = ""

    def __init__(self, file_path = None):
        if file_path is None:
            return

        statinfo = os.stat(file_path)

        self.ctime_s = int(statinfo.st_ctime)
        self.ctime_ns = int(statinfo.st_ctime_ns % 1e9)

        self.mtime_ns = int(statinfo.st_mtime_ns % 1e9)
        self.mtime_s = int(statinfo.st_mtime)

        self.dev = statinfo.st_dev

        self.ino = statinfo.st_ino

        self.mode = statinfo.st_mode

        self.uid = statinfo.st_uid
        self.gid = statinfo.st_gid
        self.size = statinfo.st_size

        with open(file_path, "r", encoding='utf-8') as input_file:
            read_file = input_file.read()
            read_file = f"blob {self.size}\0{read_file}"
            self.sha1 = hashlib.sha1(read_file.encode()).hexdigest()

        # A 16-bit 'flags' field split into:
        self.assume_valid = 0
        self.extended = 0
        self.stage = (0, 0)
        # Note - this assumes that file_path is relative to the worktree path
        self.name_len = len(file_path)

        self.path_name = file_path

    def write(self, index_file, ver_num):
        """Save this entry to a file

        Saves this index entry to a memory mapped Git index file. The entry is assumed to be
        formattted as specified by the docs [1|4]. Note that the format was extended in Version
        3 and then further in Version 4.

        Args:
            index_file - memory mapped Git index file to write to
            ver_num - version number for the this index file (available in index header)
        """
        index_file.write(self.print_to_bytes(ver_num))

    def print_to_bytes(self, ver_num):
        """Pack this index entry as a bytes object
        """
        data_format = "! " + "I"

        # The last time a file's metadata changed
        contents = struct.pack(data_format, self.ctime_s)
        contents += struct.pack(data_format, self.ctime_ns)

        # The last time a file's data changed
        contents += struct.pack(data_format, self.mtime_s)
        contents += struct.pack(data_format, self.mtime_ns)

        # The ID of device containing this file
        contents += struct.pack(data_format, self.dev)

        # The file's inode number
        contents += struct.pack(data_format, self.ino)

        # 32-bit mode, split into (high to low bits)
        contents = contents + struct.pack(data_format, self.mode)

        # stat(2) data
        contents += struct.pack(data_format, self.uid)
        contents += struct.pack(data_format, self.gid)
        contents += struct.pack(data_format, self.size)

        # Object name (SHA-1 ID) for the represented object. We are using
        # SHA-1, which are 160 bits wide. That's 20 bytes.
        contents = contents + binascii.unhexlify(self.sha1.encode())

        # A 16-bit 'flags' field split into (high to low bits)
        flags = 0
        # 1-bit assume-valid
        flags = int(self.assume_valid) << 16
        # 1-bit extended, must be 0 in version 2
        flags |= int(self.extended) << 15
        # 2-bit stage (?)
        flags |= int(self.stage[0]) << 14
        flags |= int(self.stage[1]) << 13
        flags |= self.name_len

        contents += struct.pack("!H", flags)

        # 62 bytes so far
        len_in_b = 62

        # (Version 3 or later) A 16-bit field, only applicable if the
        # "extended flag" above is 1, split into (high to low bits).
        if self.extended and (ver_num >= 3):
            extra_flags = 0
            # 1-bit reserved for future
            extra_flags |= int(self.reserved) << 16
            # 1-bit skip-worktree flag (used for sparse checkout)
            extra_flags |= int(self.skip_worktree) << 15
            # 1-bit intent-to-add flag (used by "git add -N")
            extra_flags |= int(self.intent_to_add) << 14

            contents += struct.pack("!H", extra_flags)

            len_in_b += 2

        # Entry path name (variable length) relative to top level directory
        # (without leading slash).
        assert ver_num != 4, "Writing self path name for `Version 4` not yet implemented."
        contents += self.path_name.encode("utf-8")
        len_in_b += len(self.path_name)

        # 1-8 nul bytes as necessary to pad the self to a multiple of
        # eight bytes while keeping the name NUL-terminated.  (Version 4)
        # In version 4, the padding after the pathname does not exist.
        if ver_num != 4:
            pad_len_b = (8 - (len_in_b % 8)) or 8
            num_written_null_bytes = 0
            for _ in range(pad_len_b):
                data_packed = struct.pack('B', 0)
                contents += data_packed
                num_written_null_bytes += len(data_packed)
            assert num_written_null_bytes == pad_len_b, "Error, failed to write padded bits"

        return contents

    def read(self, index_file, ver_num):
        """Read Git index entry from a file

        Reads index from the input memory mapped Git index file. The entry is
        assumed to be formatted as specified by the docs [1|4]. The data is
        saved in `self`.  Note that the format was extended in Version 3 and
        then further in Version 4.

        Args:
            index_file - memory mapped Git index file to read from
            ver_num - version number for the this index file (available in index header)
        """
        # The last time a file's metadata changed
        self.ctime_s = read_from_mmapped_file(index_file, "I")
        self.ctime_ns = read_from_mmapped_file(index_file, "I")

        # The last time a file's data changed
        self.mtime_s = read_from_mmapped_file(index_file, "I")
        self.mtime_ns = read_from_mmapped_file(index_file, "I")

        # The ID of device containing this file
        self.dev = read_from_mmapped_file(index_file, "I")

        # The file's inode number
        self.ino = read_from_mmapped_file(index_file, "I")

        # 32-bit mode, split into (high to low bits)
        self.mode = read_from_mmapped_file(index_file, "I")

        # stat(2) data
        self.uid = read_from_mmapped_file(index_file, "I")
        self.gid = read_from_mmapped_file(index_file, "I")
        self.size = read_from_mmapped_file(index_file, "I")

        # Object name (SHA-1 ID) for the represented object. We are using
        # SHA-1, which are 160 bits wide. That's 20 bytes.
        self.sha1 = binascii.hexlify(index_file.read(
            GIT_CHECKSUM_SIZE_BYTES)).decode("ascii")

        # A 16-bit 'flags' field split into (high to low bits)
        flags = read_from_mmapped_file(index_file, "H")
        # 1-bit assume-valid
        self.assume_valid = bool(flags & (0b10000000 << 8))
        # 1-bit extended, must be 0 in version 2
        self.extended = bool(flags & (0b01000000 << 8))
        # 2-bit stage (?)
        stage_one = bool(flags & (0b00100000 << 8))
        stage_two = bool(flags & (0b00010000 << 8))
        self.stage = stage_one, stage_two

        # 12-bit name length, if the length is less than 0xFFF (else, 0xFFF)
        self.name_len = flags & 0xFFF

        # 62 bytes so far
        len_in_b = 62

        # (Version 3 or later) A 16-bit field, only applicable if the
        # "extended flag" above is 1, split into (high to low bits).
        if self.extended and (ver_num >= 3):
            extra_flags = read_from_mmapped_file(index_file, "H")
            # 1-bit reserved for future
            self.reserved = bool(extra_flags & (0b10000000 << 8))
            # 1-bit skip-worktree flag (used for sparse checkout)
            self.skip_worktree = bool(extra_flags & (0b01000000 << 8))
            # 1-bit intent-to-add flag (used by "git add -N")
            self.intent_to_add = bool(extra_flags & (0b00100000 << 8))
            # 13-bits unused, must be zero
            unused = extra_flags & (0b00011111 << 8)
            assert not unused, "Exp"
            unused = extra_flags & (0b11111111)
            assert not unused, "Exp"

            len_in_b += 2

        # Entry path name (variable length) relative to top level directory
        # (without leading slash).
        assert ver_num != 4, "Reading self path name for `Version 4` not yet implemented."
        if self.name_len < 0xFFF:
            self.path_name = index_file.read(
                self.name_len).decode("utf-8", "replace")
            len_in_b += self.name_len
        else:
            # Do it the hard way
            raise Exception("GFG: Long path names are not supported")

        # 1-8 nul bytes as necessary to pad the self to a multiple of
        # eight bytes while keeping the name NUL-terminated.  (Version 4)
        # In version 4, the padding after the pathname does not exist.
        if ver_num != 4:
            pad_len_b = (8 - (len_in_b % 8)) or 8
            null_bytes = index_file.read(pad_len_b)
            assert set(null_bytes) == {0}, f"padding contained non-NUL: {null_bytes}"

class IndexTreeCacheExt():
    """Represents a Git tree cache extension. This is very well documented in
    [5] """
    num_bytes_before_data = 8

    def __init__(self, tree_cache_extension=None):
        if tree_cache_extension not in (None, b''):
            self.entries = self.__parse(tree_cache_extension)
            return

        self.ext_length = 0
        self.signature = ""
        self.entries = []

    def __parse(self, extension):
        """Parse the tree cache extension"""

        # Extension signature
        self.signature = extension[0:4].decode("ascii")
        assert self.signature == "TREE", "Not a Git tree cache extension"

        # 32-bit size of the extension
        data_format_for_int = "! I"
        self.ext_length = struct.unpack(data_format_for_int, extension[4:8])[0]

        # Extension data
        te_entries = []

        # Index into the data that's being read
        idx = IndexTreeCacheExt.num_bytes_before_data
        while idx < IndexTreeCacheExt.num_bytes_before_data + self.ext_length:
            # Read NUL-terminated path component (relative to its parent
            # directory)
            null_char_after_path = extension.find(b'\x00', idx)
            patch_component = extension[idx:null_char_after_path].decode("ascii")

            # Read ASCII decimal number of entries in the index that is
            # covered by the tree this entry represents (entry_count). Skip the
            # space (ASCII 32) that follows it.
            idx = null_char_after_path + 1
            space_char_after_entry_count = extension.find(b' ', idx)
            entry_count = int(extension[idx:space_char_after_entry_count].decode("ascii"))

            # Read ASCII decimal number that represents the number of subtrees
            # this tree has
            idx = space_char_after_entry_count + 1
            num_subtries = extension[idx:idx+1].decode("ascii")

            # Read a newline (ASCII 10)
            idx += 1
            new_line_char = extension[idx:idx+1].decode("ascii")
            assert new_line_char == '\n', \
                    f"Expecting a new line character, got {new_line_char}"
            idx += 1

            # If this entry has been invalided, save it and move to the next
            # one ...
            if entry_count == -1:
                te_entries.append((patch_component, entry_count, num_subtries, None))
                continue

            # ... otherwise read object name for the object that would result
            # from writing this span of index as a tree
            object_name_bytes = \
                    binascii.hexlify(extension[idx:idx+GIT_CHECKSUM_SIZE_BYTES])
            object_name = object_name_bytes.decode("ascii")
            idx += GIT_CHECKSUM_SIZE_BYTES
            te_entries.append((patch_component, entry_count, num_subtries, object_name))

        return te_entries

    def print_to_bytes(self):
        """Pack this extension as a bytes object"""
        if self.ext_length == 0:
            return b''

        contents = self.signature.encode()
        contents += struct.pack("! I", self.ext_length)

        for entry in self.entries:
            if entry[0] != '':
                contents += entry[0].encode()
            # Null character after the path
            contents += struct.pack("! c", b'\x00')
            # ASCII decimal number of entries in the index that is covered by
            # the tree this entry represents (entry_count)
            contents += str(entry[1]).encode()
            # A space (ASCII 32)
            contents += struct.pack("! c", b'\x20')
            # ASCII decimal number that represents the numbe rof subtrees this
            # tree has
            # NOTE: num_subtries could be more than one character!
            contents += str(entry[2]).encode()
            # A newline (ASCII 10)
            contents += struct.pack("! c", b'\x0A')
            # Object name for the object that would result from writhing this
            # span of index as a tree
            if entry[1] != GIT_INVALID_ENTRY_COUNT:
                contents += binascii.unhexlify(entry[3].encode())

        return contents

    def invalidate(self, path):
        """ When a path is updated in index, Git invalidates all nodes of the
        recursive cache tree corresponding to the parent directories of that
        path.

        Limitations:
            * only the specified path is invalided (sub-directories are ignored)
        """
        for idx, entry in enumerate(self.entries):
            if entry[0] != path:
                continue

            entry_list = list(entry)

            # ASCII decimal number of entries in the index that is covered by
            # the tree this entry represents (entry_count)
            entry_count_num_ascii_chars = len(str(entry_list[1]))
            entry_list[1] = GIT_INVALID_ENTRY_COUNT

            # Object name for the object that would result from writhing this
            # span of index as a tree
            entry_list[3] = None
            self.entries[idx] = tuple(entry_list)
            self.ext_length -= (GIT_CHECKSUM_SIZE_BYTES +
                entry_count_num_ascii_chars - GIT_NUM_OF_ASCII_CHARS_INVALID_EC)


    def validate(self):
        """Validate the contents stored in this extension
        """
        contents = self.print_to_bytes()
        if (len(contents) == 0) and self.ext_length == 0:
            return

        assert len(contents) ==\
                self.ext_length + IndexTreeCacheExt.num_bytes_before_data,\
                "GFG: Invalid cache tree extension length"


if __name__ == "__main__":
    sys.exit(1)
