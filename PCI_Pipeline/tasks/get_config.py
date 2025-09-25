from prefect import task
from processor_ci.config_generator import generate_processor_config


# Clone and generate config and shell files
@task
def generate_config_files(repo_url: str, repo_name: str):
    """
    Generates processor configuration files by cloning the specified repository and invoking the config generator.

    Args:
        repo_url (str): The URL of the repository to clone.
        repo_name (str): The name of the repository, used for naming the config file.

    Returns:
        int: Returns 0 upon successful completion.
    """
    generate_processor_config(
        repo_url,
        config_file_path=f"processor_ci.config.test.{repo_name}",
        add_config=True,
        plot_graph=False,
        no_llama=False
    )
    return 0