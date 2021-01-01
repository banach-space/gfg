# vindex.py
'''Library for representing, reading and editing Git index files.

This library implements classes represent Git index files. The provided methods
will all you to easily read/parse and modify/write index files. See [1] for
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
'''

import binascii
import mmap
import struct
import os
import sys

from pprint import pprint

CHECKSUM_SIZE_BYTES = 20


def read_from_mmapped_file(mmaped_file, format_char):
    """Reads an integer from a memory mapped file

    Reads, unpacks and returns an integer from a memory mapped file. The size
    of the integer to read is specified via a format char (documented in [2]).
    As per `Git index format` [1], all binary numbers are in network byte
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
    per `Git index format` [1], all binary numbers are in network byte order.
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
    """Represents one physical `Git index format` [1] file

    This class encapsulates a `Git index format` [1] file. Use it to read,
    parse, modify and save such files. It follows the official specification -
    any divergences are either annotated or guarded with exceptions. Any
    attempt to read or write a file in a format that's not supported will raise
    an exceptions. These are documented in the respective methods. See also the
    list of limitations documented in the module docstring.
    """
    header = None
    entries = []
    extensions = None
    checksum = None
    index_file_name = None

    def __init__(self, filename):
        self.index_file_name = filename

    def validate(self):
        assert len(self.entries) == self.header.num_entries, "GFG: The index header and actual contents are inconsistent."

    def parse(self):
        with open(self.index_file_name, "rb") as index_file_obj:
            index_file = mmap.mmap(
                index_file_obj.fileno(), 0, prot=mmap.PROT_READ)

            # Parse header
            self.header = IndexHeader()
            self.header.read(index_file)

            # Parse index entries
            self.entries = []
            for entry_idx in range(self.header.num_entries):
                entry = IndexEntry()
                entry.read(index_file, self.header.ver_num)
                self.entries.append((entry_idx, entry))

            # Parse extensions - not really supported
            index_len = len(index_file)

            num_bytes_remaining = (
                index_len - CHECKSUM_SIZE_BYTES) - index_file.tell()
            self.extensions = index_file.read(num_bytes_remaining)

            # Parse checksum
            self.checksum = binascii.hexlify(
                index_file.read(CHECKSUM_SIZE_BYTES)).decode("ascii")

            index_file.close()

    def print_to_file(self, filename=None):
        if filename is None:
            filename = self.index_file_name

        with open(filename, "wb") as index_file:
            # print(len(self.entries))

            self.header.write(index_file)
            # print(self.header.__dict__)

            for entry in self.entries:
                # print(entry[1].__dict__)
                entry[1].write(index_file, self.header.ver_num)

            index_file.write(self.extensions)
            index_file.write(binascii.unhexlify(self.checksum.encode()))
            index_file.close()

    def print_to_stdout(self):
        pprint(self.header.__dict__)

        for entry in self.entries:
            print("[entry]")
            pprint(entry[1].__dict__)

        print("[checksum]")
        pprint(self.checksum)

    def get_entry_by_filename(self, file_to_retrieve):
        _, file_name = os.path.split(file_to_retrieve)
        matching_entries = [entry for entry in self.entries
                            if os.path.split(entry[1].path_name)[1] == file_name]

        if len(matching_entries) == 1:
            return matching_entries[0]
        else:
            raise Exception(
                "GFG: More than one path matches the query. Resolution not yet support")


class IndexHeader(object):
    # 4-byte signature, b"DIRC"
    signature = None
    # 4-byte version number
    ver_num = None
    # 32-bit number of index entries, i.e. 4-byte
    num_entries = None

    def write(self, index_file):
        index_file.write(self.signature.encode())

        write_to_mmapped_file(index_file, self.ver_num, "I")

        write_to_mmapped_file(index_file, self.num_entries, "I")

    def read(self, index_file):
        self.signature = index_file.read(4).decode("ascii")
        assert self.signature == "DIRC", "Not a Git index file"

        self.ver_num = read_from_mmapped_file(index_file, "I")
        assert self.ver_num in {
            2, 3, 4}, f"Unsupported version: {self.ver_num}"

        self.num_entries = read_from_mmapped_file(index_file, "I")


class IndexEntry(object):
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
    assume_valid = None
    extended = None
    stage = {None, None}
    name_len = None

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
    path_name = None

    def write(self, index_file, ver_num):
        # The last time a file's metadata changed
        write_to_mmapped_file(index_file, self.ctime_s, "I")
        write_to_mmapped_file(index_file, self.ctime_ns, "I",)

        # The last time a file's data changed
        write_to_mmapped_file(index_file, self.mtime_s, "I")
        write_to_mmapped_file(index_file, self.mtime_ns, "I")

        # The ID of device containing this file
        write_to_mmapped_file(index_file, self.dev, "I")

        # The file's inode number
        write_to_mmapped_file(index_file, self.ino, "I")

        # 32-bit mode, split into (high to low bits)
        write_to_mmapped_file(index_file, self.mode, "I")

        # stat(2) data
        write_to_mmapped_file(index_file, self.uid, "I")
        write_to_mmapped_file(index_file, self.gid, "I")
        write_to_mmapped_file(index_file, self.size, "I")

        # Object name (SHA-1 ID) for the represented object. We are using
        # SHA-1, which are 160 bits wide. That's 20 bytes.
        index_file.write(binascii.unhexlify(self.sha1.encode()))

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

        write_to_mmapped_file(index_file, flags, "H")

        # 62 bytes so far
        self_len_in_b = 62

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

            write_to_mmapped_file(index_file, extra_flags, "H")

            self_len_in_b += 2

        # Entry path name (variable length) relative to top level directory
        # (without leading slash).
        assert ver_num != 4, "Writing self path name for `Version 4` not yet implemented."
        index_file.write(self.path_name.encode("utf-8"))
        self_len_in_b += len(self.path_name)

        # 1-8 nul bytes as necessary to pad the self to a multiple of
        # eight bytes while keeping the name NUL-terminated.  (Version 4)
        # In version 4, the padding after the pathname does not exist.
        if ver_num != 4:
            pad_len_b = (8 - (self_len_in_b % 8)) or 8
            num_written_null_bytes = 0
            for _ in range(pad_len_b):
                # write(index_file, "", "x")
                data_packed = struct.pack("x")
                num_written_null_bytes += index_file.write(data_packed)
            assert num_written_null_bytes == pad_len_b, "Error, failed to write padded bits"

    def read(self, index_file, ver_num):
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
            CHECKSUM_SIZE_BYTES)).decode("ascii")

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
        self_len_in_b = 62

        # (Version 3 or later) A 16-bit field, only applicable if the
        # "extended flag" above is 1, split into (high to low bits).
        if self.extended and (ver_num >= 3):
            self.extra_flags = read_from_mmapped_file(index_file, "H")
            # 1-bit reserved for future
            self.reserved = bool(self.extra_flags & (0b10000000 << 8))
            # 1-bit skip-worktree flag (used for sparse checkout)
            self.skip_worktree = bool(self.extra_flags & (0b01000000 << 8))
            # 1-bit intent-to-add flag (used by "git add -N")
            self.intent_to_add = bool(self.extra_flags & (0b00100000 << 8))
            # 13-bits unused, must be zero
            unused = self.extra_flags & (0b00011111 << 8)
            assert not unused, "Exp"
            unused = self.extra_flags & (0b11111111)
            assert not unused, "Exp"

            self_len_in_b += 2

        # Entry path name (variable length) relative to top level directory
        # (without leading slash).
        assert ver_num != 4, "Reading self path name for `Version 4` not yet implemented."
        if self.name_len < 0xFFF:
            self.path_name = index_file.read(
                self.name_len).decode("utf-8", "replace")
            self_len_in_b += self.name_len
        else:
            # Do it the hard way
            raise Exception("GFG: Long path names are not supported")

        # 1-8 nul bytes as necessary to pad the self to a multiple of
        # eight bytes while keeping the name NUL-terminated.  (Version 4)
        # In version 4, the padding after the pathname does not exist.
        if ver_num != 4:
            pad_len_b = (8 - (self_len_in_b % 8)) or 8
            nul_bytes = index_file.read(pad_len_b)
            assert set(nul_bytes) == {0}, "padding contained non-NUL"


if __name__ == "__main__":
    sys.exit(1)
