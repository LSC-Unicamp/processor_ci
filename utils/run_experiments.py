import os
import subprocess
import shutil
from pathlib import Path

REPO_FILE = 'repositories.txt'
MODELS_FILE = 'models.txt'
CONFIG_GENERATOR = 'config_generator.py'
TIMEOUT = 600  # 10 minutos

# Leitura dos repositórios e modelos
with open(REPO_FILE, 'r', encoding='utf-8') as f:
    repositories = [line.strip() for line in f if line.strip()]

with open(MODELS_FILE, 'r', encoding='utf-8') as f:
    models = [line.strip() for line in f if line.strip()]

for model in models:
    model_dir = Path('experiment') / model
    logs_dir = model_dir / 'logs'
    model_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    for repo in repositories:
        # Deriva o nome do processador da URL do repositório
        processor_name = repo.rstrip('/').split('/')[-1]

        output_log_path = logs_dir / f'{processor_name}.log'
        with open(output_log_path, 'w', encoding='utf-8') as log_file:
            cmd = [
                'python',
                CONFIG_GENERATOR,
                '-c',
                '-u',
                repo,
                '-m',
                model,
                '-p',
                str(model_dir),
                '-a',
            ]

            try:
                print(f'Rodando: {processor_name} com modelo {model}')
                subprocess.run(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    timeout=TIMEOUT,
                    check=False,  # continuamos mesmo se o comando falhar
                )
            except subprocess.TimeoutExpired:
                log_file.write(
                    f'\n[ERROR] Timeout após {TIMEOUT} segundos ao rodar {processor_name} com modelo {model}.\n'
                )
            except Exception as e:
                log_file.write(
                    f'\n[ERROR] Falha ao executar {processor_name} com modelo {model}: {e}\n'
                )

        # Remove a pasta temp/ após execução
        if os.path.exists('temp'):
            try:
                shutil.rmtree('temp')
            except Exception as e:
                print(f"Erro ao apagar 'temp/' após {processor_name}: {e}")
