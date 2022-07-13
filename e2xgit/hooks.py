import os
from typing import Any, Dict, Literal

from notebook.services.contents.manager import ContentsManager
from traitlets.config import Config

from .e2xrepo import E2xRepo, InvalidGitRepositoryError
from .filemanager import E2xFileContentsManager, FileOperations
from .utils import get_status


def post_file_op_commit_hook(
    contents_manager: ContentsManager,
    action: Literal[FileOperations.DELETE, FileOperations.RENAME, FileOperations.SAVE],
    options: Dict[str, Any],
) -> None:
    """Hook that is called when a file operation was performed

    Args:
        contents_manager (ContentsManager): The contents manager instance
        action (FileOperations): The file operation
        options (Dict[str, Any]): A dictionary containing information about the file operation
    """
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


def configure_e2xgit(config: Config) -> None:
    """Configure Jupyter notebook to use the E2xFileContentsManager
    and commit after every file operation

    Args:
        config (Config): The Jupyter notebook configuration object
    """
    E2xFileContentsManager.post_file_op_hook = post_file_op_commit_hook
    config.NotebookApp.contents_manager_class = E2xFileContentsManager
