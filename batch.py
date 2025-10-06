import os
import json
import subprocess

simulable_path = "config/script_correct"
non_simulable_path = "config/script_wrong"

for path in [simulable_path]:
    for file in os.listdir(path):
        if file.endswith(".json"):
            with open(os.path.join(path, file), "r") as f:
                config = json.load(f)
                name = config.get("name")
                url = config.get("repository")

                if url:
                    process = subprocess.Popen(
                        ["python3", "config_generator_core.py", "-n", "-u", url],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    stdout, stderr = process.communicate()
                    if process.returncode == 0:
                        print(f"Successfully processed {url}")
                    else:
                        print(f"Error processing {url}: {stderr.decode().strip()}")

