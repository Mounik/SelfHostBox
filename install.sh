#!/bin/bash
# SelfHostBox Installer
set -e

echo "=== SelfHostBox Installer ==="

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Install dependencies
apt-get update
apt-get install -y python3 python3-pip docker.io docker-compose git

# Create directories
mkdir -p /opt/selfhostbox/{apps,data,backups}
mkdir -p /opt/selfhostbox/traefik

# Setup Traefik
cat > /opt/selfhostbox/traefik/docker-compose.yml << 'EOF'
version: "3.8"
services:
  traefik:
    image: traefik:v2.10
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - selfhostbox
    restart: unless-stopped

networks:
  selfhostbox:
    external: true
EOF

# Create network
docker network create selfhostbox 2>/dev/null || true

# Clone SelfHostBox
cd /opt
if [ -d "selfhostbox" ]; then
    cd selfhostbox && git pull
else
    git clone https://github.com/Mounik/SelfHostBox.git selfhostbox
fi

cd /opt/selfhostbox

# Install Python deps
pip3 install -r requirements.txt

# Create database
python3 -c "from backend.app import db; db.create_all()"

# Start Traefik
cd /opt/selfhostbox/traefik
docker-compose up -d

# Install systemd service
cp systemd/selfhostbox.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable selfhostbox
systemctl start selfhostbox

echo ""
echo "=== SelfHostBox installed ==="
echo "Access: http://your-server:8080"
echo "Configure: edit /opt/selfhostbox/config/config.yml"