#!/usr/bin/env bash
set -e

PYTHON_ENV=".venv"

if ! command -v python3 &>/dev/null; then
  echo "❌ Python3 não encontrado. Instale antes de continuar."
  exit 1
fi

if [ ! -d "$PYTHON_ENV" ]; then
  echo "🧪 Criando ambiente virtual..."
  python3 -m venv "$PYTHON_ENV"
fi

source "$PYTHON_ENV/bin/activate"
pip install --upgrade pip

if [ -f "requirements.txt" ]; then
  echo "📦 Instalando dependências..."
  pip install -r requirements.txt
fi

echo "✅ Ambiente configurado com sucesso!"
deactivate
