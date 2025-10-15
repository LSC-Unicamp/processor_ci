import argparse
from ..tasks.repo import RepoStruct
from ..tasks.config import ConfigStruct
from ..tasks.cocotb_setup import create_makefile

def simulation_flow(processor_name: str):
    create_makefile(processor_name)

def main_flow(repo_url: str):
    repo = RepoStruct(repo_url, base_dir="processors")
    repo_path = repo.repo_path
    
    config = ConfigStruct(destination_path="config", repo=repo)
    config_path = config.config_path
    
    # Gera config (pegar nova versão do config_generator)
    
    # Gera o RTL (Perguntar se para o Julio)

    simulation_flow(repo_path.split('/')[-1])


def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Clone a Git repository.")
    parser.add_argument("--repo-url", type=str, required=True, 
                        help="The URL of the Git repository to clone.")
    args = parser.parse_args()

    # Clone the repository and generate config and shell files
    main_flow(args.repo_url)
    return 0

if __name__ == "__main__":
    main()