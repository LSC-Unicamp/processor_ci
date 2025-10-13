import os
from pathlib import Path


class RepoStruct:
    """Simple struct that wraps cloning/holding repo info for tasks.

    On construction it will compute the repo name and ensure the repository is
    present under the requested base directory (cloning it if necessary).
    """

    def __init__(self, url: str, base_dir: str):
        self.url = url
        self.base_dir = base_dir
        self.repo_name = self.extract_repo_name(url)
        self.repo_path = self.clone_repo(url, base_dir)

    def extract_repo_name(self, url: str) -> str:
        """Extract repository name from a URL (strip trailing .git).

        Args:
            url: Repository URL.

        Returns:
            Repository folder name (without .git).
        """
        return url.split('/')[-1].replace('.git', '')

    def clone_repo(self, url: str, base_dir: str) -> str:
        """Ensure the repository exists under base_dir/processors and return path.

        If the directory does not exist the function will attempt to clone it
        using GitPython. The git import is deferred to runtime to avoid import
        time failures when GitPython is not available.
        """
        try:
            import git
        except Exception as e:
            raise ImportError(
                "GitPython is required to clone repositories. Install it with `pip install GitPython`."
            ) from e

        base_norm = os.path.normpath(base_dir)
        if os.path.basename(base_norm) == "processors":
            processors_dir = base_norm
        else:
            processors_dir = os.path.join(base_dir, "processors")
        Path(processors_dir).mkdir(parents=True, exist_ok=True)

        repo_name = self.extract_repo_name(url)
        repo_path = os.path.join(processors_dir, repo_name)
        if not os.path.exists(repo_path):
            git.Repo.clone_from(url, repo_path)

        return repo_path