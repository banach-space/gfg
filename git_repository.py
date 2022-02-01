#!/usr/bin/env python3
"""
Implements a class that represents a Git repository

[1] Git Repository Format Versions:
    https://github.com/git/git/blob/master/Documentation/technical/repository-version.txt
[2] git-config documentation:
    https://git-scm.com/docs/git-config
[3] https://codewords.recurse.com/issues/three/unpacking-git-packfiles
"""

import configparser
import os
import glob
from pathlib import Path

class GitRepository():
    """A git repository"""

    git_subdir_name = ".git"

    @staticmethod
    def get_root_git_dir(git_subdir):
        """ Find the root Git directory for the given repo subdirectory

        Git can be invoked from any subdirectory within a Git project. This
        method returns the root Git directory corresponding the the repository
        containing `git_subdir`.

        INPUT:
            git_subdir - a subdirectory within a Git repository

        RETURN:
            Git repository root directory or None if not a Git repository
        """
        # Start by assuming that this is the root Git directory
        repo_path = git_subdir

        while not repo_path.joinpath(repo_path, GitRepository.git_subdir_name).exists() \
                and repo_path != repo_path.parent:
            repo_path = repo_path.parent

        if repo_path.joinpath(repo_path, GitRepository.git_subdir_name).exists():
            return repo_path

        return None

    def is_object_in_repo(self, object_hash: str):
        """Check whether this repo contains an object with SHA matching object_hash?

        INPUT:
            object_hash - Git object hash to get the path for
        RETURN:
            True if `object_hash` exists, False otherwise
        """
        # Calculate the file path from the object hash
        file_dir = Path(self.git_dir) / "objects" / object_hash[0:2]
        file_path = Path(file_dir) / object_hash[2:]

        list_of_matching_files = glob.glob(str(file_path) + "*")
        if len(list_of_matching_files) == 1:
            return True

        return False

    def get_object_path(self, object_hash: str):
        """ Get the directory and the full path of a Git object

        This method generates Git repository path based on the object hash. It
        assumes that the corresponding objects alrady exists in the repo.

        Note that the object hash could be provided in its full form (e.g.
        2c250da0045dc138bf12e2f0217bd30d375b44d7), or in a shortened form (e.g.
        2c25). Both versions are accepted, but "short" hash must uniquely
        identify the object within this repo.

        LIMITATION: Packfiles [3] are not supported.

        Note that the object hash could be provided in its full form (e.g.
        2c250da0045dc138bf12e2f0217bd30d375b44d7), or a shortened form (e.g.
        2c250da0045). The shortened form is simply expanded to its full form.

        INPUT:
            object_hash - Git object hash to get the path for
        RETURN:
            dir, path - the directory and the full path of the object
            corresponding to the input Git object
        """
        assert self.is_object_in_repo(object_hash)

        # Calculate the file path from the object hash
        file_dir = Path(self.git_dir) / "objects" / object_hash[0:2]
        file_path = Path(file_dir) / object_hash[2:]

        # If the hash was provided by the user, it might have been a shortened
        # version. If that's the case, self.file_path needs to recalculated.
        list_of_matching_files = glob.glob(str(file_path) + "*")
        if len(list_of_matching_files) == 1:
            file_path = Path(list_of_matching_files[0])

        return (file_dir, file_path)

    def __init__(self, directory=".", force_init=True):
        # The worktree directory for this repository
        self.worktree_dir = Path(os.path.normpath(directory))
        # The .git directory for this repository
        self.git_dir = self.worktree_dir.joinpath(".git")
        # Contents of the Git config file for this repository (i.e. .git/config)
        self.git_config = None

        # Find the _top_ working/Git directory
        if not os.path.isdir(self.git_dir):
            repo_path = GitRepository.get_root_git_dir(self.worktree_dir)
            if repo_path:
                self.worktree_dir = repo_path
                self.git_dir = os.path.join(self.worktree_dir, ".git")

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

        # Create .git/description
        with open(self.get_git_file_path("description"), "w", encoding='utf-8') as desc_file:
            desc_file.write(
                    "Unnamed repository; edit this file 'description'"
                    "to name the repository.\n")

        # Create .git/HEAD
        with open(self.get_git_file_path("HEAD"), "w", encoding='utf-8') as head_file:
            head_file.write("ref: refs/heads/master\n")

        # Create .git/config
        self.create_default_config()
        with open(self.get_git_file_path("config"), "w", encoding='utf-8') as config_file:
            self.git_config.write(config_file)

        # Print this for consistency with Git
        print(f"Initialized empty Git repository in {os.path.abspath(self.git_dir)}")

    @staticmethod
    def get_repo(git_repo_subdir):
        """Retrieve the Git repository for 'git_repo_subdir'

        It returns an instance of GitRepository that corresponds to the input
        Git repository subdirectory. If the input directory is not a
        (sub)directory in a Git repository, return None.

        INPUT:
            Directory for which to find a Git repository
        RETURN:
            GitRepository on success, None on failure
        """
        path =  Path(os.path.abspath(git_repo_subdir))

        path = GitRepository.get_root_git_dir(path)
        if path is None:
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
