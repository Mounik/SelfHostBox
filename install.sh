#!/bin/bash
set -e

echo "=== SelfHostBox Installer ==="

if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

DISTRO_ID=""
if [ -f /etc/os-release ]; then
    DISTRO_ID=$(grep '^ID=' /etc/os-release | cut -d= -f2 | tr -d '"')
fi

echo "Detected distro: ${DISTRO_ID:-unknown}"

install_deps_debian() {
    apt-get update
    apt-get install -y python3 python3-pip python3-venv docker.io docker-compose-plugin git curl
}

install_deps_fedora() {
    dnf install -y python3 python3-pip docker docker-compose-plugin git curl
}

install_deps_arch() {
    pacman -Sy --noconfirm python python-pip docker docker-compose-plugin git curl
}

case "$DISTRO_ID" in
    ubuntu|debian|linuxmint|pop)
        install_deps_debian
        ;;
    fedora|rhel|centos|rocky|alma)
        install_deps_fedora
        ;;
    arch|manjaro|endeavouros)
        install_deps_arch
        ;;
    *)
        echo "Unsupported distro. Please install manually: python3, pip, docker, docker-compose-plugin, git"
        exit 1
        ;;
esac

mkdir -p /opt/selfhostbox/{apps,data,backups,config,traefik}

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ "$SCRIPT_DIR" != "/opt/selfhostbox" ]; then
    if [ -d /opt/selfhostbox/.git ]; then
        cd /opt/selfhostbox && git pull
    else
        git clone https://github.com/Mounik/SelfHostBox.git /opt/selfhostbox
    fi
fi

cat > /opt/selfhostbox/traefik/docker-compose.yml << 'EOF'
version: "3.8"
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL:-admin@example.com}"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--api.dashboard=true"
      - "--api.insecure=false"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - selfhostbox
    restart: unless-stopped
    labels:
      - "traefik.enable=false"

networks:
  selfhostbox:
    external: true
EOF

docker network create selfhostbox 2>/dev/null || true

if [ ! -f /opt/selfhostbox/config/config.yml ]; then
    cp /opt/selfhostbox/config/config.yml.example /opt/selfhostbox/config/config.yml
    echo ""
    echo "!! Edit /opt/selfhostbox/config/config.yml with your domain and email !!"
fi

python3 -m venv /opt/selfhostbox/.venv
/opt/selfhostbox/.venv/bin/pip install -r /opt/selfhostbox/requirements.txt

cd /opt/selfhostbox/traefik
docker compose up -d

cp /opt/selfhostbox/systemd/selfhostbox.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable selfhostbox
systemctl restart selfhostbox

echo ""
echo "=== SelfHostBox installed ==="
echo "Access: http://your-server:8080"
echo "Configure: edit /opt/selfhostbox/config/config.yml"