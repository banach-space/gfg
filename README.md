Git From Glasgow
================

[![unittests](https://github.com/banach-space/gfg/workflows/Ubuntu-unittests/badge.svg?branch=main)](https://github.com/banach-space/gfg/actions?query=workflow%3AUbuntu-unittests+branch%3Amain)
[![pylint](https://github.com/banach-space/gfg/workflows/Ubuntu-pylint/badge.svg)](https://github.com/banach-space/gfg/actions?query=workflow%3AUbuntu-pylint+branch%3Amain)

A custom implementation of Git - for those curious how stuff works!

**Git From Glasgow** is a collection of Python scripts that implement the key
Git data structures and the command line user interface. To avoid confusion,
the equivalent of `git` in **Git From Glasgow** is called `gfg`. It follows a
few basic design principles:

* **Simplicity** - Only selected, most popular Git commands are implemented
  (sufficient to create a repository and to commit new changes)
* **Compatibility with Git** - Every Git command that is supported by Gfg is
  fully compatibly with a similar command in Git (i.e. `git` and `gfg` are
  interchangeable)
* **Verifiability** - Compatibility with Git is tested using
  [bats-core](https://github.com/bats-core/bats-core)


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
While I have tried to make **GFG** OS-agnostic, I have not been able to test it
on Windows yet. Please let me know if you experience any issues!

Supported Git Commands
==================
A list of implemented Git options with the supported flags (note that Git
equivalents of these options normally support more flags):
### Basic commands
* `gfg init` ([documentation](https://git-scm.com/docs/git-init))
* `gfg add <files>` ([documentation](https://git-scm.com/docs/git-add))
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
a new option), please open an
[issue](https://github.com/banach-space/gfg/issues) to track this.
Contributions in the form of bug reports, suggestions and general feedback are
also much appreciated!

References
===========
A list of my favourite resources on Git internals that I have found incredibly
helpful while working on **Git From Glasgow**:
* _"Write yourself a Git!"_, Thibault Polge ([link](https://wyag.thb.lt/))
* _"Git File format"_,  Jelmer Vernooĳ ([link](https://www.dulwich.io/docs/tutorial/file-format.html#git-file-format))
* _"Git from the inside out"_, Mary Rose Cook ([link](https://maryrosecook.com/blog/post/git-from-the-inside-out))
* _"Unpacking Git packfiles"_, Aditya Mukerjee ([link](https://codewords.recurse.com/issues/three/unpacking-git-packfiles))
