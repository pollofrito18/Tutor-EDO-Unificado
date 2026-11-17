#!/usr/bin/env bash
set -eu
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  printf '%s\n' 'Primero crea el entorno: python3.12 -m venv .venv' 'Después instala: .venv/bin/python -m pip install -r requirements.txt'
  exit 1
fi
exec .venv/bin/python -m streamlit run app.py
