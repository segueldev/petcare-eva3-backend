#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 || $# -ne 1 || ! $1 =~ ^[a-zA-Z0-9][a-zA-Z0-9.-]*$ ]]; then
    echo "Uso: sudo bash deploy/install.sh IP_PUBLICA_O_DNS" >&2
    exit 1
fi
public_host=$1
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
app_dir=/opt/petcare/app
env_file=/etc/petcare.env

apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y python3-venv postgresql nginx openssl curl
systemctl enable --now postgresql
id petcare >/dev/null 2>&1 || useradd --system --no-create-home --shell /usr/sbin/nologin petcare

install -d -m 0755 "$app_dir"
cp -r -- "$source_dir"/{manage.py,requirements.txt,petcare,clinic} "$app_dir/"
python3 -m venv /opt/petcare/venv
/opt/petcare/venv/bin/python -m pip install -r "$app_dir/requirements.txt"

if [[ ! -f $env_file ]]; then
    secret=$(openssl rand -hex 48)
    db_password=$(openssl rand -hex 32)
    install -m 0600 /dev/null "$env_file"
    cat > "$env_file" <<ENV
DJANGO_SECRET_KEY=$secret
DJANGO_ALLOWED_HOSTS=$public_host,localhost,127.0.0.1
POSTGRES_DB=petcare
POSTGRES_USER=petcare
POSTGRES_PASSWORD=$db_password
POSTGRES_HOST=127.0.0.1
ENV
else
    sed -i "s/^DJANGO_ALLOWED_HOSTS=.*/DJANGO_ALLOWED_HOSTS=$public_host,localhost,127.0.0.1/" "$env_file"
fi
source "$env_file"
if [[ $(runuser -u postgres -- psql -Atqc "SELECT 1 FROM pg_roles WHERE rolname='petcare'") != 1 ]]; then
    runuser -u postgres -- psql -v ON_ERROR_STOP=1 <<SQL
CREATE ROLE petcare WITH LOGIN PASSWORD '$POSTGRES_PASSWORD';
SQL
fi
if [[ $(runuser -u postgres -- psql -Atqc "SELECT 1 FROM pg_database WHERE datname='petcare'") != 1 ]]; then
    runuser -u postgres -- createdb -O petcare petcare
fi

install -d -o petcare -g petcare -m 0755 "$app_dir/staticfiles"
bash "$source_dir/deploy/manage.sh" check
bash "$source_dir/deploy/manage.sh" migrate --noinput
bash "$source_dir/deploy/manage.sh" preparar_roles
bash "$source_dir/deploy/manage.sh" collectstatic --noinput
install -m 0644 "$source_dir/deploy/petcare.service" /etc/systemd/system/petcare.service
systemctl daemon-reload
systemctl enable --now petcare
systemctl restart petcare
sed "s/__PUBLIC_HOST__/$public_host/g" "$source_dir/deploy/petcare.nginx" > /etc/nginx/sites-available/petcare
ln -sfn /etc/nginx/sites-available/petcare /etc/nginx/sites-enabled/petcare
nginx -t
systemctl enable --now nginx
systemctl reload nginx
curl --fail --silent --show-error --retry 5 --retry-delay 1 --retry-all-errors \
    -o /dev/null -H "Host: $public_host" http://127.0.0.1/cuenta/login/
echo "PetCare respondió en Nginx para http://$public_host/. Comprueba el enlace desde fuera de EC2."
