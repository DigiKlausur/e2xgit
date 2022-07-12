import os
import shutil
from typing import Dict, List

from git import GitCommandError, InvalidGitRepositoryError, Repo

from .utils import get_author


class E2xRepo:
    def __init__(self, path: str, create_if_not_exists: bool = False):
        """Create a git repository instance

        Args:
            path (str): Current working directory
            create_if_not_exists (bool, optional): If the current path is not a git repository initialize one. Defaults to False.

        Raises:
            InvalidGitRepositoryError: If the path is not part of a git repositry and create_if_not_exists is set to False
        """
        assert os.path.isdir(path), f"Path: {path} does not exist"
        self.path = path
        try:
            self.repo = Repo(path, search_parent_directories=True)
        except InvalidGitRepositoryError:
            if create_if_not_exists:
                self.repo = Repo.init(path)
                self.create_gitignore()
            else:
                raise InvalidGitRepositoryError(f"{path} is not a valid repository")

        self.author = get_author(self.repo)

    def get_path(self, path: str) -> str:
        """Get the path relative to the repo root

        Args:
            path (str): path

        Returns:
            str: path relative to repo root
        """
        if not os.path.isabs(path):
            path = os.path.join(self.path, path)
        return os.path.relpath(path, start=self.repo.working_tree_dir)

    def status(self) -> Dict[str, List[str]]:
        """Get the status of a repository

        Args:
            repo (Repo): The repository instance

        Returns:
            Dict[str, List[str]]: A dictionary containing list of files
        """
        return dict(
            untracked=self.repo.untracked_files,
            staged=[item.a_path for item in self.repo.index.diff("HEAD")],
            unstaged=[item.a_path for item in self.repo.index.diff(None)],
        )

    def create_gitignore(self):
        here = os.path.dirname(__file__)
        shutil.copy(
            os.path.join(here, "assets", ".gitignore"),
            os.path.join(self.repo.working_tree_dir, ".gitignore"),
        )
        self.repo.git.add([".gitignore"])
        self.repo.git.commit(
            [
                '-m "Add .gitignore"',
                f"--author='{self.author.name} <{self.author.email}>'",
                ".gitignore",
            ]
        )

    def is_untracked(self, file: str) -> bool:
        """Is the file untracked?

        Args:
            file (str): path to file

        Returns:
            bool: True if untracked
        """
        path = self.get_path(file)
        return path in self.status()["untracked"]

    def add(self, file: str) -> None:
        """Add a file to the repository

        Args:
            file (str): The path to the file
        """
        if self.is_untracked(file):
            self.repo.git.add([self.get_path(file)])

    def commit(self, file: str, message: str = None, add_if_untracked=False) -> None:
        """Commit a single file

        Args:
            file (str): Path to the file
            message (str, optional): The commit message to use. Defaults to None.
            add_if_untracked (bool, optional): Add the file if it is untracked. Defaults to False.

        Raises:
            GitCommandError: If the file is untracked and add_if_untracked is set to False
        """
        path = self.get_path(file)
        status = self.status()
        if message is None:
            status = self.status()
            if path in status["untracked"]:
                message = f"Add {path}"
            elif path in status["staged"]:
                message = f"Update {path}"
            elif path in status["unstaged"]:
                message = f"Delete {path}"

        if path in status["untracked"]:
            if not add_if_untracked:
                raise GitCommandError(
                    command="git commit",
                    status=f"The file {file} is currently untracked!",
                )
            else:
                self.add(file)

        self.repo.git.commit(
            [
                f"-m '{message}'",
                f"--author='{self.author.name} <{self.author.email}>'",
                path,
            ]
        )

    def get_unstaged(self) -> List[str]:
        """Get the unstaged files

        Returns:
            List[str]: List of unstaged files
        """
        return [item.a_path for item in self.repo.index.diff(None)]
