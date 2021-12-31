# gfg
Git From Glasgow

[![unittests](https://github.com/banach-space/gfg/workflows/Ubuntu-unittests/badge.svg?branch=main)](https://github.com/banach-space/gfg/actions?query=workflow%3AUbuntu-unittests+branch%3Amain)
[![pylint](https://github.com/banach-space/gfg/workflows/Ubuntu-pylint/badge.svg)](https://github.com/banach-space/gfg/actions?query=workflow%3AUbuntu-pylint+branch%3Amain)

Table of Contents
=================
* [Supported commands](#supported-commands)
* [Contributing](#contributing)
* [References](#references)

Supported commands
===========
A list of implemented Git options with the supported flags (note that Git
equivalents of these options normally support more flags):
* `gfg init`
* `gfg add <files>`
* `git cat-file (-t | -p | <type> ) <object>`
* `gfg hash-object [-w] [--stdin] <file>`
* `gfg log`

Contributing
===========
Pull requests are very welcome! If you want to make a larger contribution (e.g.
a new option), please open an
[issue](https://github.com/banach-space/gfg/issues) to track this.
Contributions in the form of bug reports, suggestions and general feedback are
also much appreciated!

References
===========
* _"Write yourself a Git!"_, Thibault Polge ([link](https://wyag.thb.lt/))
* _"Git File format"_,  Jelmer Vernooĳ ([link](https://www.dulwich.io/docs/tutorial/file-format.html#git-file-format))
* _"Git from the inside out"_, Mary Rose Cook ([link](https://maryrosecook.com/blog/post/git-from-the-inside-out))
* _"Unpacking Git packfiles"_, Aditya Mukerjee ([link](https://codewords.recurse.com/issues/three/unpacking-git-packfiles))
