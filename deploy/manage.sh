#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
    echo "Ejecuta con sudo." >&2
    exit 1
fi
cd /opt/petcare/app
set -a
source /etc/petcare.env
set +a
exec runuser -u petcare -- /opt/petcare/venv/bin/python manage.py "$@"
