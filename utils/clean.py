"""Main function to remove unwanted keys from config.json"""

import json

# Load the JSON from the config.json file
with open("config.json", "r", encoding="utf-8") as file:
    data = json.load(file)

# Remove the unwanted keys
for core in data["cores"].values():
    core.pop("modules", None)
    core.pop("module_graph", None)
    core.pop("module_graph_inverse", None)
    core.pop("non_tb_files", None)

# Save the new JSON to a new file
with open("config2.json", "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)

print(
    "The unwanted keys have been removed and the new file has been saved as config2.json."
)
