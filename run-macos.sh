#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
fi

echo "Paste your OPENAI_API_KEY when prompted. Leave blank to edit .env manually."
read -rsp "OPENAI_API_KEY (optional): " OPENAI_KEY
echo
if [ -n "${OPENAI_KEY}" ]; then
  python - "$OPENAI_KEY" <<'PY'
import sys
key = sys.argv[1]
path = ".env"
lines = []
with open(path, "r", encoding="utf-8") as fh:
    lines = fh.readlines()
found = False
for idx, line in enumerate(lines):
    if line.startswith("OPENAI_API_KEY="):
        lines[idx] = f"OPENAI_API_KEY={key}\n"
        found = True
        break
if not found:
    lines.insert(0, f"OPENAI_API_KEY={key}\n")
with open(path, "w", encoding="utf-8") as fh:
    fh.writelines(lines)
PY
fi

echo "Save any changes to .env, then press Enter to launch the agent."
read -r

until python main.py; do
  echo "Agent exited with errors. Reinstalling dependencies and trying again..."
  pip install -r requirements.txt
  echo "Press Enter once you've addressed any issues to retry."
  read -r
done
