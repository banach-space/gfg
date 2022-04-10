Git From Glasgow
================

[![unittests](https://github.com/banach-space/gfg/workflows/Ubuntu-unittests/badge.svg?branch=main)](https://github.com/banach-space/gfg/actions?query=workflow%3AUbuntu-unittests+branch%3Amain)
[![pylint](https://github.com/banach-space/gfg/workflows/Ubuntu-pylint/badge.svg)](https://github.com/banach-space/gfg/actions?query=workflow%3AUbuntu-pylint+branch%3Amain)

A custom implementation of Git - for those curious how stuff works!

**Git From Glasgow** is a collection of Python scripts that implement the key
Git data structures and the command line user interface. It follows a
few basic design principles: 

* **Simplicity** - Only selected, most popular Git commands are available.
* **Compatibility with Git** - Every command is fully compatible with its Git
  equivalent.
* **Standalone** - There are no external dependencies beyond Python.

To avoid confusion, the command-line interface in **Git From Glasgow** is
called `gfg` rather than `git`.

### About
**Git From Glasgow** implements the key elements of Git:

* [index file](https://git-scm.com/docs/index-format#_cache_tree) (see [git_index.py](https://github.com/banach-space/gfg/blob/main/git_index.py))
* various [Git objects](https://matthew-brett.github.io/curious-git/git_object_types.html) (e.g. blob, commit and commit, see [git_object.py](https://github.com/banach-space/gfg/blob/main/git_object.py))
* Git command-line interface, which in **Git From Glasgow** is called `gfg` (see [gfg](https://github.com/banach-space/gfg/blob/main/gfg))

Although only selected Git commands are supported (see [Supported Git
Commands](#supported-git-commands)), the available functionality is sufficient
to:

* initialise a fresh repository (`gfg init`),
* add and commit new changes (e.g. `gfg add` and `gfg commit`),
* read the contents of an existing repository (e.g. `gfg log` and `gfg
  cat-file`).

The main goal of **Git From Glasgow** is to help understand _how Git works_
(including the fine details). It is not meant as a replacement for **Git**.
Indeed, some key and more advanced features are not available (e.g.
[packfiles](https://git-scm.com/book/en/v2/Git-Internals-Packfiles)). For this
reason, it is best to experiment with **GFG** in a dedicated test repository.

### Table of Contents
* [Installing and Testing](#installing-and-testing)
* [Supported Git Commands](#supported-git-commands)
* [Contributing](#contributing)
* [References](#references)

Installing and Testing
======================
In order to use **Git From Glasgow**, you will require Python 3 (>= 3.6.9).  In
order to run the Git conformance tests, you will also have to install
[bats-core](https://github.com/bats-core/bats-core). Below is a full set-up
that should work on most Unix platforms (tested on Ubuntu and MacOS):
```bash
# Clone GFG, add `gfg` to your path
git clone https://github.com/banach-space/gfg
export PATH=path/to/gfg:$PATH
# Clone bats-core so that you can run the conformance tests, add `bats` to your path
git clone https://github.com/bats-core/bats-core.git
export PATH=path/to/bats-core:$PATH
cd gfg/test
# Run Git conformance tests
bats -t .
# Run GFG unit tests
PYTHONPATH="../" python3 -m unittest
```
While I have strived to make **GFG** OS-agnostic, I have not been able to test
it on Windows yet. Please let me know if you experience any issues!

Supported Git Commands
==================
Below is a list of Git options supported by **Git From Glasgow** with the
supported flags (note that Git equivalents of these options normally support
more flags):
### Basic commands
* `gfg init` ([documentation](https://git-scm.com/docs/git-init))
* `gfg add <files>` ([documentation](https://git-scm.com/docs/git-add))
* `gfg commit -m message` ([documentation](https://git-scm.com/docs/git-commit))
* `gfg log` ([documentation](https://git-scm.com/docs/git-log))

### Less basic commands
* `git cat-file (-t | -p | <type> ) <object>`
  ([documentation](https://git-scm.com/docs/git-cat-file))
* `gfg hash-object [-w] [--stdin] <file>` ([documentation](https://git-scm.com/docs/git-hash-object))
* `gfg write-tree` ([documentation](https://git-scm.com/docs/git-write-tree))
* `gfg commit-tree -m message <tree>` ([documentation](https://git-scm.com/docs/git-commit-tree))

Contributing
===========
Pull requests are very welcome! If you want to make a larger contribution (e.g.
add a new option), please open an
[issue](https://github.com/banach-space/gfg/issues) to track this.

Contributions in the form of bug reports, suggestions and general feedback are
also much appreciated!

ToDo
======
Here's a list of things that I would like to add support for (PRs welcome!):

* testing on Windows (may require some refactoring to make **GFG** actually
  work on Windows)
* `gfg rm` ([documentation](https://git-scm.com/docs/git-rm))
* `gfg branch` ([documentation](https://git-scm.com/docs/git-branch))
* `gfg checkout` ([documentation](https://git-scm.com/docs/git-checkout))
* `gfg push` ([documentation](https://git-scm.com/docs/git-push))
* more tests

I'm also aware that there might be some inconsistencies in the code that would
be nice to fix:

* `hash`, `sha` and `object_hash` are used interchangeably. Choose one instead.
* Classes in
  [git_object.py](https://github.com/banach-space/gfg/blob/main/git_object.py)
  have slightly inconsistent APIs.
* Reduce the use of class variables (e.g. in `IndexEntry`).

References
===========
A list of my favourite resources on Git internals. I have found these
incredibly helpful while working on **Git From Glasgow**.
* _"Write yourself a Git!"_, Thibault Polge ([link](https://wyag.thb.lt/))
* _"Git File format"_,  Jelmer Vernooĳ ([link](https://www.dulwich.io/docs/tutorial/file-format.html#git-file-format))
* _"Git from the inside out"_, Mary Rose Cook ([link](https://maryrosecook.com/blog/post/git-from-the-inside-out))
* _"Unpacking Git packfiles"_, Aditya Mukerjee ([link](https://codewords.recurse.com/issues/three/unpacking-git-packfiles))
