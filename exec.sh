#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ -n "${PYTHON:-}" ]]; then
  python_command=("$PYTHON")
elif [[ -x .venv/Scripts/python.exe ]]; then
  python_command=(.venv/Scripts/python.exe)
elif [[ -x .venv/bin/python ]]; then
  python_command=(.venv/bin/python)
elif command -v python >/dev/null 2>&1; then
  python_command=(python)
elif command -v python3 >/dev/null 2>&1; then
  python_command=(python3)
elif command -v py.exe >/dev/null 2>&1; then
  python_command=(py.exe -3)
else
  echo 'Python nao encontrado no Bash. Execute exec.ps1 no PowerShell.' >&2
  exit 1
fi
if [[ ! -f final-SP.zip ]]; then
  echo 'Gere final-SP.zip com regulator.py antes de executar.' >&2
  exit 1
fi
# Sem exclusoes ou concentracoes por padrao.
"${python_command[@]}" generator.py 10000 180 1719304546 1719701874 "Distrito-SP.zip" "" --weighted_shapefile "final-SP.zip"
