#!/usr/bin/env python3
"""
Implements a class that represents a Git repository

[1] Git Repository Format Versions:
    https://github.com/git/git/blob/master/Documentation/technical/repository-version.txt
[2] git-config documentation:
    https://git-scm.com/docs/git-config
"""

import configparser
import os

class GitRepository():
    """A git repository"""

    # The .git directory for this repository
    git_dir = None
    # The worktree directory for this repository
    worktree_dir = None
    # Contents of the Git config file for this repository (i.e. .git/config)
    git_config = None

    def create_git_dir(self, *directory):
        '''Create a sub-directory in the .git directory

        Creates a sub-directory in .git based. Treats every component in
        *directory as a subdirectory of the preceding item in the list.
        '''
        full_path = os.path.join(*directory)
        if os.path.exists(full_path):
            raise Exception(f"Git dirctory {directory} already exists!")

        os.makedirs(os.path.join(self.git_dir, *directory))

    def get_git_file_path(self, git_file):
        '''Get the path for the requested git_file

        This is just a convenice method to contextualise calls to os.path.join.
        '''
        return os.path.join(self.git_dir, git_file)

    def check_git_config(self):
        '''Validate the Git config file for this repository

        This functions does a minimal sanity-check of the Git config file for
        this repository.
        '''
        # Read the configuration file
        self.git_config = configparser.ConfigParser()
        config_file = self.get_git_file_path("config")

        # Check that it esists
        if not os.path.exists(config_file):
            raise Exception("Repository local configuration file missing")

        self.git_config.read([config_file])

        # Check the repository version - only Version '0' is supported, see [1]
        format_version = int(self.git_config.get("core", "repositoryformatversion"))
        if format_version != 0:
            raise Exception(f"Unsupported repositoryformatversion {format_version}")

    def create_default_config(self):
        '''Create the default Git config for this repository'''
        self.git_config = configparser.ConfigParser()

        # The Git config section for the following fields. `git init` only
        # creates the `core` section.
        self.git_config.add_section("core")

        # From [2],  the repository format and layout version. `git init` sets
        # this to 0.
        self.git_config.set("core", "repositoryformatversion", "0")
        # From [2], filemode tells Git if the executable bit of files in the
        # working tree is to be honored. Git sets this to true. Gfg does not
        # (to keep things simple)
        self.git_config.set("core", "filemode", "false")
        # From [2], if true this repository is assumed to be bare and has no
        # working directory associated with it. Git sets this to `false` by
        # default.
        self.git_config.set("core", "bare", "false")

    def __init__(self, directory):
        self.worktree_dir = directory
        self.git_dir = os.path.join(directory, ".git")

        if os.path.isdir(self.git_dir):
            print(f"Reinitialized existing Git repository in "
                    f"{os.path.abspath(self.git_dir)}/")
            self.check_git_config()
            return

        # Create standard Git directories. Note that we are not creating:
        #   * .git/hooks
        #   * .git/info
        # as `git` would.
        os.makedirs(".git")
        self.create_git_dir("branches")
        self.create_git_dir("objects")
        self.create_git_dir("refs", "tags")
        self.create_git_dir("refs", "heads")

        # .git/description
        with open(self.get_git_file_path("description"), "w") as desc_file:
            desc_file.write(
                    "Unnamed repository; edit this file 'description'"
                    "to name the repository.\n")

        # .git/HEAD
        with open(self.get_git_file_path("HEAD"), "w") as head_file:
            head_file.write("ref: refs/heads/master\n")

        # .git/config
        self.create_default_config()
        with open(self.get_git_file_path("config"), "w") as config_file:
            self.git_config.write(config_file)

        print(f"Initialized empty Git repository in {os.path.abspath(self.git_dir)}")
