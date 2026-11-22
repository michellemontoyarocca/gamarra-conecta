#!/usr/bin/env bash
set -euo pipefail

cd /srv/gamarra-conecta
test "$(id -un)" = gamarra
test "$(git branch --show-current)" = main
test -z "$(git status --porcelain)"

previous=$(git rev-parse HEAD)
venv=/srv/gamarra-conecta-home/venv
if test -f instance/gamarra.sqlite3; then
  cp -p instance/gamarra.sqlite3 "/srv/gamarra-backups/predeploy-$(date -u +%Y%m%dT%H%M%SZ).sqlite3"
fi

git fetch origin main
git merge --ff-only origin/main

if ! "$venv/bin/python" -m pip install -r requirements.txt || ! sudo -n systemctl restart gamarra-conecta; then
  echo 'Falló la instalación o el reinicio; restaurando la versión anterior' >&2
  git reset --hard "$previous"
  "$venv/bin/python" -m pip install -r requirements.txt
  sudo -n systemctl restart gamarra-conecta
  exit 1
fi

for attempt in $(seq 1 12); do
  if systemctl is-active --quiet gamarra-conecta && curl -fsS http://127.0.0.1:8018/salud | grep -q '"estado":"ok"'; then
    echo "Despliegue verificado: $(git rev-parse --short HEAD)"
    exit 0
  fi
  sleep 2
done

echo 'Falló la comprobación de salud; restaurando la versión anterior' >&2
git reset --hard "$previous"
"$venv/bin/python" -m pip install -r requirements.txt
sudo -n systemctl restart gamarra-conecta
exit 1
