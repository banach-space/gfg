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
from pathlib import Path

class GitRepository():
    """A git repository"""

    git_subdir_name = ".git"

    def __init__(self, directory=".", force_init=True):
        # The worktree directory for this repository
        self.worktree_dir = Path(os.path.normpath(directory))
        # The .git directory for this repository
        self.git_dir = self.worktree_dir.joinpath(".git")
        # Contents of the Git config file for this repository (i.e. .git/config)
        self.git_config = None

        # Find the _top_ working directory
        if not os.path.isdir(self.git_dir):
            path = self.worktree_dir
            while path != path.parent:
                path = path.parent
                if os.path.isdir(os.path.join(path, ".git")):
                    self.worktree_dir = path.absolute()
                    self.git_dir = os.path.join(self.worktree_dir, ".git")
                    break

        # Check whether this an exiisting repo
        if os.path.isdir(self.git_dir):
            if force_init:
                print(f"Reinitialized existing Git repository in "
                        f"{os.path.abspath(self.git_dir)}/")
            self.load_git_config()
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
        with open(self.get_git_file_path("description"), "w", encoding='utf-8') as desc_file:
            desc_file.write(
                    "Unnamed repository; edit this file 'description'"
                    "to name the repository.\n")

        # .git/HEAD
        with open(self.get_git_file_path("HEAD"), "w", encoding='utf-8') as head_file:
            head_file.write("ref: refs/heads/master\n")

        # .git/config
        self.create_default_config()
        with open(self.get_git_file_path("config"), "w", encoding='utf-8') as config_file:
            self.git_config.write(config_file)

        print(f"Initialized empty Git repository in {os.path.abspath(self.git_dir)}")

    @staticmethod
    def get_repo(input_dir):
        """Retrieve the Git repository for 'input_dir'

        This method assumes that the input directory is within a Git
        repository. It returns an instance of GitRepository that corresponds to
        that repository. If the input directory is not a (sub)directory in a
        Git repository this method returns None.

        Args:
            Directory for which to find a Git repository
        Returns:
            GitRepository on success, None on failure
        """
        input_dir = os.path.abspath(input_dir)
        path = Path(input_dir).absolute()

        while not path.joinpath(path, GitRepository.git_subdir_name).exists() \
                and path != path.parent:
            path = path.parent

        if not path.joinpath(path, GitRepository.git_subdir_name).exists():
            print("fatal: not a git repository (or any of the parent directories): .git")
            return None

        return GitRepository(path, False)


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

    def load_git_config(self):
        '''Load the Git config file for this repository

        This functions also does a minimal sanity-check of the Git config file
        for this repository.
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
