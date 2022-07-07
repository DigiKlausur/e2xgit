import os

from notebook.services.contents.manager import ContentsManager
from traitlets.config import Config

from .e2xrepo import E2xRepo, InvalidGitRepositoryError


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
    except InvalidGitRepositoryError:
        contents_manager.log.info("[E2X Git] No repository found!")

    repo.commit(os_path, add_if_untracked=True)


def configure_post_save_hook(config: Config) -> None:
    """Given a Jupyter notebook config add the post_save_commit_hook

    Args:
        config (Config): The Jupyter notebook config
    """
    config.FileContentsManager.post_save_hook = post_save_commit_hook
