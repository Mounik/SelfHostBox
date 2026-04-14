#!/bin/bash
# SelfHostBox Proxmox Install Script
# Usage: curl -sL https://raw.githubusercontent.com/Mounik/SelfHostBox/main/install-proxmox.sh | sudo bash

set -e

echo "=== SelfHostBox Installer for Proxmox/Debian ==="

# Update and install dependencies
echo "[1/5] Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv git curl docker.io docker-compose-plugin

# Enable Docker
systemctl enable docker
systemctl start docker

# Create SelfHostBox directory
echo "[2/5] Setting up SelfHostBox..."
mkdir -p /opt/selfhostbox
cd /opt/selfhostbox

# Clone or update
if [ -d ".git" ]; then
    git pull
else
    rm -rf /opt/selfhostbox/*
    git clone https://github.com/Mounik/SelfHostBox.git /tmp/shb
    mv /tmp/shb/* /opt/selfhostbox/
    rm -rf /tmp/shb
fi

# Create directories
mkdir -p apps data backups config traefik

# Create Docker network
docker network create selfhostbox 2>/dev/null || true

# Create Traefik config
echo "[3/5] Configuring Traefik..."
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
    labels:
      - "traefik.enable=false"

networks:
  selfhostbox:
    external: true
EOF

# Start Traefik
cd /opt/selfhostbox/traefik && docker compose up -d

# Install Python dependencies
echo "[4/5] Installing Python dependencies..."
cd /opt/selfhostbox
pip install --break-system-packages -r requirements.txt

# Create systemd service
echo "[5/5] Creating systemd service..."
cat > /etc/systemd/system/selfhostbox.service << 'EOF'
[Unit]
Description=SelfHostBox
After=docker.service network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/selfhostbox
Environment=PYTHONPATH=/opt/selfhostbox
ExecStart=/usr/bin/python3 /opt/selfhostbox/backend/app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable selfhostbox
systemctl start selfhostbox

echo ""
echo "=== SelfHostBox installed successfully! ==="
echo "Access: http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "Create admin user with:"
echo "  curl -X POST http://localhost:8080/api/auth/setup \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"username\":\"admin\",\"password\":\"YourPassword123\"}'"
echo ""
echo "Logs: journalctl -u selfhostbox -f"
