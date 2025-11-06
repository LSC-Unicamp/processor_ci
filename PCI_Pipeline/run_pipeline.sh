#!/usr/bin/env bash
set -e

CONFIG_FILE=""
PARALLEL=false
MAX_JOBS=0
declare -A STATUS
declare -A LOG_PATHS

# --- Função de ajuda ---
usage() {
  echo "Uso: $0 <config.json> [opções]"
  echo
  echo "  <config.json>     Caminho do arquivo de configuração JSON"
  echo "  --parallel, -p    Executa pipelines em paralelo"
  echo "  --jobs, -j <N>    Limita o número de pipelines rodando em paralelo (ativa modo paralelo automaticamente)"
  echo
  exit 1
}

# --- Parse dos argumentos ---
while [[ $# -gt 0 ]]; do
  case $1 in
    --parallel|-p)
      PARALLEL=true
      shift
      ;;
    --jobs|-j)
      PARALLEL=true
      MAX_JOBS="$2"
      shift 2
      ;;
    -*)
      echo "Opção desconhecida: $1"
      usage
      ;;
    *)
      CONFIG_FILE="$1"
      shift
      ;;
  esac
done

if [ -z "$CONFIG_FILE" ]; then
  usage
fi

# --- Verifica dependências ---
for cmd in jq python3 date; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Erro: o comando '$cmd' não está instalado."
    exit 1
  fi
done

# --- Diretório de logs ---
timestamp=$(date +"%Y-%m-%d_%H-%M-%S")
log_dir="logs/$timestamp"
mkdir -p "$log_dir"

# --- Lê opções padrão ---
cleanup_default=$(jq -r '.default_options.cleanup' "$CONFIG_FILE")
verify_default=$(jq -r '.default_options.verify_versions' "$CONFIG_FILE")
skip_config_default=$(jq -r '.default_options.skip_config_generation' "$CONFIG_FILE")
skip_rtl_default=$(jq -r '.default_options.skip_rtl_generation' "$CONFIG_FILE")
skip_sim_default=$(jq -r '.default_options.skip_simulation' "$CONFIG_FILE")
skip_synth_default=$(jq -r '.default_options.skip_synthesis' "$CONFIG_FILE")

# --- Função para rodar um core ---
run_core() {
  local core="$1"
  local repo_url=$(jq -r ".cores[\"$core\"].github" "$CONFIG_FILE")

  local cleanup=$(jq -r ".cores[\"$core\"].pipeline_options.cleanup // \"$cleanup_default\"" "$CONFIG_FILE")
  local verify=$(jq -r ".cores[\"$core\"].pipeline_options.verify_versions // \"$verify_default\"" "$CONFIG_FILE")
  local skip_config=$(jq -r ".cores[\"$core\"].pipeline_options.skip_config_generation // \"$skip_config_default\"" "$CONFIG_FILE")
  local skip_rtl=$(jq -r ".cores[\"$core\"].pipeline_options.skip_rtl_generation // \"$skip_rtl_default\"" "$CONFIG_FILE")
  local skip_sim=$(jq -r ".cores[\"$core\"].pipeline_options.skip_simulation // \"$skip_sim_default\"" "$CONFIG_FILE")
  local skip_synth=$(jq -r ".cores[\"$core\"].pipeline_options.skip_synthesis // \"$skip_synth_default\"" "$CONFIG_FILE")

  local log_file="${log_dir}/${core}.log"
  LOG_PATHS["$core"]="$log_file"

  echo "→ [${core}] Iniciando pipeline..."
  {
    echo "=== Executando pipeline para $core ==="
    echo "Data: $(date)"
    echo "Repositório: $repo_url"
    echo "Opções:"
    echo "  cleanup=$cleanup"
    echo "  verify=$verify"
    echo "  skip_config=$skip_config"
    echo "  skip_rtl=$skip_rtl"
    echo "  skip_simulation=$skip_sim"
    echo "  skip_synthesis=$skip_synth"
    echo "---------------------------------------------"

    python3 -m PCI_Pipeline.flows.main_flow \
      --repo-url "$repo_url" \
      $( [ "$cleanup" = "true" ] && echo "--cleanup" ) \
      $( [ "$verify" = "true" ] && echo "--verify-updates" ) \
      $( [ "$skip_config" = "true" ] && echo "--skip-config" ) \
      $( [ "$skip_rtl" = "true" ] && echo "--skip-rtl" ) \
      $( [ "$skip_sim" = "true" ] && echo "--skip-simulation" ) \
      $( [ "$skip_synth" = "true" ] && echo "--skip-synthesis" )

    echo
    echo "✔ [$core] Concluído com sucesso em $(date)."
  } &> "$log_file"

  local exit_code=$?
  if [ $exit_code -eq 0 ]; then
    echo "OK" > "${log_dir}/${core}.status"
  else
    echo "ERRO" > "${log_dir}/${core}.status"
  fi
}

# --- Controle de jobs paralelos ---
job_control() {
  local running
  while true; do
    running=$(jobs -r | wc -l)
    if (( running < MAX_JOBS )); then
      break
    fi
    sleep 0.5
  done
}

# --- Execução principal ---
cores=($(jq -r '.cores | keys[]' "$CONFIG_FILE"))

echo "Iniciando pipeline com ${#cores[@]} cores..."
echo "Logs em: $log_dir"

if $PARALLEL; then
  echo "🚀 Modo paralelo ativado"
  if [ "$MAX_JOBS" -gt 0 ]; then
    echo "→ Limitado a $MAX_JOBS jobs simultâneos"
  fi

  for core in "${cores[@]}"; do
    if [ "$MAX_JOBS" -gt 0 ]; then
      job_control
    fi
    run_core "$core" &
  done
  wait
else
  echo "⚙️ Modo sequencial"
  for core in "${cores[@]}"; do
    run_core "$core"
  done
fi

# --- Resumo final ---
summary_csv="${log_dir}/summary_${timestamp}.csv"
echo "Core,Status,Log" > "$summary_csv"

echo
echo "=================== RESUMO FINAL ==================="
for core in "${cores[@]}"; do
  status=$(cat "${log_dir}/${core}.status" 2>/dev/null || echo "ERRO_DESCONHECIDO")
  log="${LOG_PATHS[$core]}"
  if [ "$status" = "OK" ]; then
    echo "✔ $core: OK"
  else
    echo "✖ $core: ERRO (ver $log)"
  fi
  echo "$core,$status,$log" >> "$summary_csv"
done
echo "===================================================="

echo
echo "📄 Resumo salvo em: $summary_csv"
echo "🗂️  Logs individuais em: $log_dir"
