from .repo import RepoStruct
# Delay importing the heavy connector module until it's needed to avoid
# import-time failures when running lightweight tasks or tests that don't
# require the connector's dependencies (colorlog, etc.).

from typing import Optional


class ConfigStruct:
    def __init__(self, destination_path: str, repo: RepoStruct):
        self.destination_path = destination_path
        self.repo = repo
        self.config_path = self.generate_config(destination_path, repo)
        self.rtl_path = self.generate_rtl(destination_path, repo)

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
            self.repo.url,
            destination_path,
            False,
            True,
            False,
            existing_repo=self.repo.repo_path
        )
        return destination_path

    def generate_rtl(self, destination_path: str, repo: RepoStruct) -> Optional[str]:
        try:
            from processor_ci_connector import main as connector_main
        except Exception as e:
            raise ImportError(
                "processor_ci_connector is required to generate RTL wrappers. "
                f"Import failed: {e}. Please install its dependencies or ensure it is on PYTHONPATH."
            )

        connector_main.build_wrapper(
            config=destination_path,
            processor=self.repo.repo_name,
            context=10,
            model='qwen3:14b',
            processor_path=self.repo.repo_path,
            output='output',
            convert=True,
            format=True,
        )
        return None
