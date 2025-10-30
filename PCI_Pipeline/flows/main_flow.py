import argparse
from ..tasks.repo import RepoStruct
from ..tasks.config import ConfigStruct
from ..tasks.cocotb_setup import create_makefile

def simulation_flow(processor_name: str):
    create_makefile(processor_name)

def main_flow(repo_url: str, cleanup: bool, verify_updates: bool, skip_config: bool, skip_rtl: bool, skip_simulation: bool, skip_synthesis: bool) -> None:
    repo = RepoStruct(repo_url, base_dir="processors")
    repo_path = repo.repo_path
    
    config = ConfigStruct(destination_path="config", repo=repo)
    config_path = config.config_path
    rtl_path = config.rtl_path
    
    simulation_flow(repo_path.split('/')[-1])


def main(
    repo_url: str, 
    cleanup: bool, 
    verify_updates: bool, 
    skip_config: bool, 
    skip_rtl: bool, 
    skip_simulation: bool, 
    skip_synthesis: bool) -> None:
    # Clone the repository and generate config and shell files
    main_flow(repo_url, cleanup, verify_updates, skip_config, skip_rtl, skip_simulation, skip_synthesis)
    return None

if __name__ == "__main__":
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Clone a Git repository.")
    parser.add_argument("--repo-url", type=str, required=True, 
                        help="The URL of the Git repository to clone.")
    parser.add_argument("--cleanup", "-c", action="store_true",
                        help="Clean up the cloned repository after processing.")
    parser.add_argument("--verify-updates", "-v", action="store_true",
                        help="Verify if there are updates in the repository.")
    parser.add_argument("--skip-config", action="store_true",
                        help="Skip configuration file generation.")
    parser.add_argument("--skip-rtl", action="store_true",
                        help="Skip RTL file generation.")
    parser.add_argument("--skip-simulation", action="store_true",
                        help="Skip simulation setup.")
    parser.add_argument("--skip-synthesis", action="store_true",
                        help="Skip synthesis setup.")
    args = parser.parse_args()
    main(args.repo_url, args.cleanup, args.verify_updates, args.skip_config, args.skip_rtl, args.skip_simulation, args.skip_synthesis)