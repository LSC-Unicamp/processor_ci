from .repo import RepoStruct


class ConfigStruct:
    def __init__(self, destination_path: str, repo: RepoStruct):
        self.destination_path = destination_path
        self.repo = repo
        self.config_path = self.generate_config(destination_path, repo)

    def generate_config(self, destination_path: str, repo: RepoStruct) -> str:
        """Generate configuration for a local repo by delegating to the top-level generator.

        This method performs a lazy import of `config_generator` so the module
        can still be imported in minimal environments.
        """
        try:
            import config_generator as cg
        except Exception:
            raise EOFError(
                "config_generator is required to generate configurations. Ensure all dependencies are installed."
            )

        # Call the generator. It returns None (side-effect) — we return the
        # destination path for convenience.
        cg.generate_processor_config(
            repo.url,
            True,
            False,
            destination_path,
            True,
            existing_repo=repo.repo_path,
        )

        return destination_path
