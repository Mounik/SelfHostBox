#!/bin/bash
# SelfHostBox Universal Installer
# Works on Ubuntu 20.04+ and Debian 11+
# Usage: curl -fsSL https://raw.githubusercontent.com/Mounik/SelfHostBox/main/install-selfhostbox.sh | bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

REPO_URL="https://github.com/Mounik/SelfHostBox.git"
INSTALL_DIR="/opt/selfhostbox"

echo -e "${GREEN}=== SelfHostBox Installer ===${NC}"
echo "Detected distro: $(lsb_release -is 2>/dev/null || echo 'unknown')"
echo ""

# Function to print status
status() {
    echo -e "${YELLOW}[*]${NC} $1"
}

success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    error "Please run as root (use sudo)"
    exit 1
fi

# Detect distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VERSION=$VERSION_ID
else
    error "Cannot detect distribution"
    exit 1
fi

status "Updating package lists..."
export DEBIAN_FRONTEND=noninteractive

# Handle apt locks gracefully
wait_for_apt() {
    local timeout=300
    local elapsed=0
    
    while fuser /var/lib/apt/lists/lock /var/lib/dpkg/lock* >/dev/null 2>&1 || pgrep -x "apt|apt-get|dpkg" >/dev/null; do
        if [ $elapsed -ge $timeout ]; then
            error "Timeout waiting for apt locks"
            # Try to clean up locks
            rm -f /var/lib/apt/lists/lock /var/lib/dpkg/lock* 2>/dev/null || true
            break
        fi
        echo -n "."
        sleep 5
        elapsed=$((elapsed + 5))
    done
    echo ""
}

# Wait for any running apt processes
wait_for_apt

# Fix any broken dpkg states
dpkg --configure -a 2>/dev/null || true

apt-get update -qq
success "Package lists updated"

# Install dependencies
status "Installing dependencies..."
apt-get install -y -qq \
    curl \
    git \
    python3 \
    python3-pip \
    python3-venv \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    software-properties-common || {
    error "Failed to install dependencies"
    exit 1
}
success "Dependencies installed"

# Install Docker
status "Installing Docker..."
if ! command -v docker &> /dev/null; then
    # Try to install docker.io from repo first (Debian/Ubuntu)
    if apt-cache show docker.io >/dev/null 2>&1; then
        apt-get install -y -qq docker.io
    else
        # Fallback to Docker's official install script
        curl -fsSL https://get.docker.com | bash
    fi
    
    # Install docker-compose
    if apt-cache show docker-compose >/dev/null 2>&1; then
        apt-get install -y -qq docker-compose
    else
        # Install docker-compose via pip as fallback
        pip3 install docker-compose
    fi
    
    systemctl enable docker
    systemctl start docker
    success "Docker installed"
else
    success "Docker already installed"
fi

# Ensure docker is running
if ! systemctl is-active --quiet docker; then
    systemctl start docker
fi

# Create directory structure
status "Creating directories..."
mkdir -p $INSTALL_DIR/{data,backups,apps,config}
success "Directories created"

# Clone or update SelfHostBox
status "Installing SelfHostBox..."
if [ -d "$INSTALL_DIR/.git" ]; then
    cd $INSTALL_DIR
    git pull -q origin main
else
    rm -rf $INSTALL_DIR
    git clone -q $REPO_URL $INSTALL_DIR
    cd $INSTALL_DIR
fi
success "SelfHostBox cloned"

# Modify install.sh to use docker-compose instead of docker-compose-plugin if needed
if [ -f "install.sh" ]; then
    sed -i 's/docker-compose-plugin/docker-compose/' install.sh 2>/dev/null || true
fi

# Create virtual environment and install dependencies
status "Setting up Python environment..."
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
success "Python environment ready"

# Fix permissions
chown -R root:root $INSTALL_DIR
chmod -R 755 $INSTALL_DIR/data

# Create systemd service file
status "Creating systemd service..."
cat > /etc/systemd/system/selfhostbox.service << 'EOF'
[Unit]
Description=SelfHostBox - Self-Hosting Platform
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/selfhostbox
Environment=PYTHONPATH=/opt/selfhostbox
Environment=SELFHOSTBOX_CONFIG=/opt/selfhostbox/config/config.yml
Environment=FLASK_ENV=production
ExecStart=/opt/selfhostbox/.venv/bin/gunicorn --bind 0.0.0.0:8080 --workers 2 --timeout 60 "backend.app:create_app()"
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create initial config if not exists
if [ ! -f "$INSTALL_DIR/config/config.yml" ]; then
    mkdir -p $INSTALL_DIR/config
    cat > $INSTALL_DIR/config/config.yml << 'EOF'
# SelfHostBox Configuration
data_dir: /opt/selfhostbox/data
backup_dir: /opt/selfhostbox/backups
apps_dir: /opt/selfhostbox/apps

# Network settings
host_ip: 0.0.0.0
port: 8080

# Security
secret_key: change-this-in-production

# Domains
base_domain: localhost
EOF
fi

# Start Traefik first
status "Starting Traefik reverse proxy..."
docker compose -f docker-compose.traefik.yml up -d || docker-compose -f docker-compose.traefik.yml up -d
success "Traefik started"

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable selfhostbox
systemctl start selfhostbox

# Wait for service to start
sleep 3

# Check if service is running
if systemctl is-active --quiet selfhostbox; then
    success "SelfHostBox service is running!"
else
    error "SelfHostBox service failed to start"
    systemctl status selfhostbox --no-pager
    exit 1
fi

# Get IP address
IP=$(hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  SelfHostBox Installed!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "🌐 Access SelfHostBox at:"
echo -e "   ${YELLOW}http://$IP:8080${NC}"
echo ""
echo -e "📁 Installation directory:"
echo -e "   ${YELLOW}$INSTALL_DIR${NC}"
echo ""
echo -e "🔧 Service commands:"
echo -e "   ${YELLOW}systemctl status selfhostbox${NC}"
echo -e "   ${YELLOW}systemctl restart selfhostbox${NC}"
echo -e "   ${YELLOW}journalctl -u selfhostbox -f${NC}"
echo ""
echo -e "${GREEN}================================${NC}"
