#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 || ! $1 =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ || ! -r $2 || ! -r $3 ]]; then
    echo "Uso: bash deploy/subir_ec2.sh IP_PUBLICA ruta_clave.pem ruta_known_hosts" >&2
    exit 1
fi

host=$1
key=$2
known_hosts=$3
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
ssh_options=(-i "$key" -o IdentitiesOnly=yes -o "UserKnownHostsFile=$known_hosts" -o StrictHostKeyChecking=yes -o ConnectTimeout=12)

tar -czf - --exclude='__pycache__' -C "$source_dir" manage.py requirements.txt petcare clinic deploy |
    ssh "${ssh_options[@]}" "ubuntu@$host" \
        'mkdir -p "$HOME/petcare-eva3" && tar -xzf - -C "$HOME/petcare-eva3"'

ssh -t "${ssh_options[@]}" "ubuntu@$host" \
    "cd petcare-eva3 && sudo bash deploy/install.sh $host && sudo bash deploy/manage.sh cargar_demo && sudo bash deploy/manage.sh createsuperuser"

printf '\nComprueba PetCare en http://%s/ y actualiza la URL verificada en README.md antes de publicar.\n' "$host"
