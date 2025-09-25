from prefect import task
import git
import os
from pathlib import Path

@task
def clone_repo(repo_url: str, base_dir: str) -> str:
    """
    Clones a git repository to a 'processors' directory inside the specified base directory.

    Args:
        repo_url (str): The URL of the git repository to clone.
        base_dir (str): The base directory where the 'processors' directory will be created.

    Returns:
        str: The path to the cloned repository.
    """
    processors_dir = os.path.join(base_dir, "processors")
    Path(processors_dir).mkdir(parents=True, exist_ok=True)

    repo_name = os.path.basename(repo_url).replace('.git', '')
    repo_path = os.path.join(processors_dir, repo_name)
    if not os.path.exists(repo_path):
        git.Repo.clone_from(repo_url, repo_path)
    
    return repo_path