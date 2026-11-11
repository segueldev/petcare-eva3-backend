#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"

python_path=${PETCARE_PYTHON:-.venv/bin/python}
if [[ ! -x $python_path && -z ${PETCARE_PYTHON:-} ]]; then
    python3 -m venv .venv
fi
if ! "$python_path" -c 'import django, rest_framework' >/dev/null 2>&1; then
    "$python_path" -m pip install -r requirements.txt
fi

# La demostración local usa su propia base y solo escucha en este equipo.
export DJANGO_DEBUG=1 PETCARE_DEV_SQLITE=1
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
export DJANGO_HTTPS=0
"$python_path" manage.py migrate --noinput
"$python_path" manage.py preparar_roles
"$python_path" manage.py cargar_demo

if ! "$python_path" manage.py shell -c 'from django.contrib.auth import get_user_model; raise SystemExit(not get_user_model().objects.filter(is_superuser=True, is_active=True).exists())' >/dev/null; then
    printf '\nCrea la contraseña de la cuenta local petcare_local cuando te la pida.\n'
    "$python_path" manage.py createsuperuser --username petcare_local --email local@example.com
fi

printf '\nAbre http://127.0.0.1:8000/ en tu navegador. Pulsa Ctrl+C para detener PetCare.\n\n'
exec "$python_path" manage.py runserver 127.0.0.1:8000
