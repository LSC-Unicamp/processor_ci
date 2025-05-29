import os
import json

config_dir = 'config'
output_file = 'repositories.txt'

repositories = []

for filename in os.listdir(config_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                repo = data.get('repository')
                if repo:
                    repositories.append(repo)
        except Exception as e:
            print(f'Erro ao processar {filename}: {e}')

with open(output_file, 'w', encoding='utf-8') as f:
    for repo in repositories:
        f.write(repo + '\n')

print(f'{len(repositories)} repositórios salvos em {output_file}')
