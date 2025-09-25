import prefect
from prefect import flow, task
import argparse
from processor_ci.PCI_Pipeline.tasks.get_config import generate_config_files

# Generate necessary config file and shell file
@flow
def config_flow(repo_url: str):
    generate_config_files(repo_url)
    # Gerar rtl

@flow
def simulation_flow():
    
    pass

@flow
def main_flow(repo_url: str):
    config_flow(repo_url)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Clone a Git repository.")
    parser.add_argument("--repo-url", type=str, required=True, 
                        help="The URL of the Git repository to clone.")
    parser.add_argument("--base-dir", type=str, required=True, 
                        help="The base directory where the 'processors' directory will be created.")
    args = parser.parse_args()

    # Clone the repository and generate config and shell files
    main_flow(args.repo_url)
    return 0

if __name__ == "__main__":
    main()