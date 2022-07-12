import os
from typing import Any, Dict

from notebook.services.contents.manager import ContentsManager
from traitlets.config import Config

from .e2xrepo import E2xRepo, InvalidGitRepositoryError
from .filemanager import FileOperations
from .utils import get_status


def post_save_commit_hook(
    model: dict, os_path: str, contents_manager: ContentsManager, **kwargs
) -> None:
    """Commit files on save

    Args:
        model (dict): The file model
        os_path (str): The absolute path to the file
        contents_manager (ContentsManager): The instance of the ContentsManager class
    """
    try:
        repo = E2xRepo(os.path.dirname(os_path))
        repo.commit(os_path, add_if_untracked=True)
    except InvalidGitRepositoryError:
        contents_manager.log.info("[E2X Git] No repository found!")


def post_file_op_commit_hook(
    contents_manager: ContentsManager, action: FileOperations, options: Dict[str, Any]
):
    repo = None
    contents_manager.log.info(contents_manager.root_dir)
    try:
        repo = E2xRepo(os.path.dirname(options["path"]))
    except InvalidGitRepositoryError:
        contents_manager.log.info(
            f"[E2X Git] No repository found for file {options['path']}"
        )
        return

    if action == FileOperations.SAVE:
        repo.commit(options["path"], add_if_untracked=True)
    elif action == FileOperations.RENAME:
        # Either git detects that the file has been renamed or it deletes and adds a file
        status = get_status(repo.repo)
        rel_path = repo.get_path(options["path"])
        if rel_path not in status["staged"]:
            # Remove old file, add and commit new file
            old_rel_path = repo.get_path(options["old_path"])
            repo.commit(old_rel_path, message=f"Remove {old_rel_path}")
        repo.commit(options["path"], add_if_untracked=True)
    elif action == FileOperations.DELETE:
        repo.commit(options["path"])


def configure_post_save_hook(config: Config) -> None:
    """Given a Jupyter notebook config add the post_save_commit_hook

    Args:
        config (Config): The Jupyter notebook config
    """
    config.FileContentsManager.post_save_hook = post_save_commit_hook
