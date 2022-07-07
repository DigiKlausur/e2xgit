import os

from git import Actor, GitCommandError, Repo


def get_author(repo: Repo) -> Actor:
    """
    Get the current author for a repository
    If the author is not set default to either the JUPYTERHUB user or the local USER

    Args:
        repo (Repo): The git repository

    Returns:
        Actor: The current author for the git repository
    """
    name, email = None, None
    try:
        name = repo.git.config("user.name")
        email = repo.git.config("user.email")
    except GitCommandError:
        name = os.getenv("JUPYTERHUB_USER")
        if name is None:
            name = os.getenv("USER")
        email = f"{name}@e2x.git"
    return Actor(name, email)
