# SelfHostBox 🏠

**One-click self-hosting platform — deploy Nextcloud, Vaultwarden, and 20+ apps in seconds**

SelfHostBox is a web UI that makes self-hosting dead simple. Choose an app, click deploy, get a working instance with SSL, backups, and automatic updates.

```bash
# Install SelfHostBox
curl -sL https://raw.githubusercontent.com/Mounik/SelfHostBox/main/install.sh | sudo bash

# Access web UI
open http://localhost:8080

# Deploy Vaultwarden in 30 seconds
# Click "Vaultwarden" → "Deploy" → Done!
```

## 🎯 Features

- **One-click deploy** — 20+ popular self-hosted apps
- **Automatic SSL** — Let's Encrypt with Traefik reverse proxy
- **Custom domains** — Use your own domain or auto-generated subdomains
- **Automatic backups** — Daily backups to local storage or S3
- **Auto-updates** — Apps update automatically (optional)
- **Resource monitoring** — See CPU/RAM usage per app
- **User management** — Multi-user with permissions
- **App store** — Browse and install new apps

## 📦 Available Apps

| Category | Apps |
|----------|------|
| **Productivity** | Nextcloud, Vaultwarden, Outline, Joplin |
| **Media** | Plex, Jellyfin, Navidrome, Photoprism |
| **Dev Tools** | Gitea, Jenkins, GitLab CE, Code-Server |
| **Monitoring** | Uptime Kuma, Portainer, Netdata |
| **Communication** | Matrix, Rocket.Chat, Mattermost |
| **Finance** | Firefly III, Actual Budget |
| **Misc** | Pi-hole, AdGuard, Home Assistant, Paperless |

## 🚀 Quick Start

### Automated Install

```bash
curl -sL https://raw.githubusercontent.com/Mounik/SelfHostBox/main/install.sh | sudo bash
```

### Manual Install

```bash
# Clone
git clone https://github.com/Mounik/SelfHostBox.git
cd SelfHostBox

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.yml.example config/config.yml
# Edit config.yml with your domain and settings

# Initialize
./selfhostbox init

# Start
./selfhostbox start

# Or as systemd service
sudo systemctl enable --now selfhostbox
```

## ⚙️ Configuration

`config/config.yml`:

```yaml
# SelfHostBox Configuration
version: "1.0"

# Network
base_domain: "selfhostbox.local"  # or your domain
traefik_network: selfhostbox

# SSL (Let's Encrypt)
ssl:
  enabled: true
  email: admin@example.com
  provider: letsencrypt  # or custom
  staging: false  # Set to true for testing

# Storage
storage:
  data_dir: /opt/selfhostbox/data
  backups_dir: /opt/selfhostbox/backups
  
# Backups
backup:
  enabled: true
  schedule: "0 2 * * *"  # Daily at 2 AM
  retention_days: 7
  # Optional: S3 backup
  s3:
    enabled: false
    bucket: selfhostbox-backups
    region: eu-west-1
    access_key: ""
    secret_key: ""

# Auto-updates
updates:
  enabled: true
  check_interval: "24h"
  auto_apply: false  # If true, updates auto-apply (dangerous)

# Apps directory
apps_dir: /opt/selfhostbox/apps

# Database (for SelfHostBox metadata)
database:
  type: sqlite  # or postgresql
  path: /opt/selfhostbox/selfhostbox.db
```

## 🖥️ Web UI

Access at `http://your-server:8080`

### Dashboard
- List of deployed apps
- Status (running, stopped, error)
- Resource usage (CPU, RAM, disk)
- Quick actions (start, stop, restart, update)

### App Store
- Browse available apps
- Search and filter by category
- One-click install
- Preview app info and requirements

### App Management
- Configure environment variables
- Set resource limits (CPU, RAM)
- Manage volumes and mounts
- View logs
- Backup/restore
- Delete with cleanup

### Domain Management
- Use auto-generated subdomain: `app-name.selfhostbox.local`
- Or custom domain: `cloud.mydomain.com`
- Automatic DNS verification
- SSL certificate status

## 📁 Project Structure

```
SelfHostBox/
├── README.md
├── requirements.txt
├── setup.py
├── selfhostbox.sh              # CLI entry point
├── install.sh                  # Automated installer
├── config/
│   ├── config.yml.example      # Configuration template
│   └── traefik.yml             # Traefik static config
├── backend/
│   ├── __init__.py
│   ├── app.py                  # Flask/FastAPI app
│   ├── models.py               # Database models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── apps.py             # App management endpoints
│   │   ├── domains.py          # Domain management
│   │   ├── backups.py          # Backup operations
│   │   └── system.py           # System info
│   ├── core/
│   │   ├── __init__.py
│   │   ├── docker.py           # Docker Compose operations
│   │   ├── traefik.py          # Traefik configuration
│   │   ├── ssl.py              # SSL certificate management
│   │   └── backup.py           # Backup engine
│   └── templates/
│       └── apps/               # App Compose templates
│           ├── nextcloud/
│           │   ├── docker-compose.yml
│           │   └── env.example
│           ├── vaultwarden/
│           ├── jellyfin/
│           └── ...
├── frontend/
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
├── systemd/
│   └── selfhostbox.service     # systemd service file
└── docs/
    ├── INSTALL.md
    ├── TROUBLESHOOTING.md
    └── API.md
```

## 🔧 API Endpoints

```
GET  /api/apps              # List deployed apps
POST /api/apps              # Deploy new app
GET  /api/apps/{id}         # App details
PUT  /api/apps/{id}         # Update app config
DELETE /api/apps/{id}      # Remove app

GET  /api/store             # Available apps in store
GET  /api/store/{app}       # App template details

POST /api/apps/{id}/start   # Start container
POST /api/apps/{id}/stop    # Stop container
POST /api/apps/{id}/restart # Restart container
POST /api/apps/{id}/backup  # Create backup
POST /api/apps/{id}/restore # Restore from backup

GET  /api/system/info       # System resources
GET  /api/system/logs       # SelfHostBox logs
```

## 🧪 Adding Custom Apps

Create `backend/templates/apps/myapp/`:

```yaml
# docker-compose.yml
version: "3.8"
services:
  app:
    image: myorg/myapp:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`${DOMAIN}`)"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
    volumes:
      - data:/data
    environment:
      - "APP_KEY=${APP_KEY}"
      
volumes:
  data:
```

```json
# manifest.json
{
  "name": "MyApp",
  "description": "Description of the app",
  "category": "productivity",
  "icon": "myapp.png",
  "version": "1.0.0",
  "ports": ["8080"],
  "env": {
    "APP_KEY": {
      "description": "Application secret key",
      "required": true,
      "default": "auto-generate"
    }
  },
  "volumes": ["data"],
  "minimum_resources": {
    "memory": "256m",
    "cpu": "0.25"
  }
}
```

## 🤝 Use Cases

- **Personal cloud** — Replace Google/Dropbox with self-hosted alternatives
- **Family server** — Photos, documents, password manager for family
- **Small business** — CRM, file sharing, communication tools
- **Developer homelab** — Git, CI/CD, monitoring stack
- **Freelance offering** — Setup self-hosted infrastructure for clients

## 💰 Pricing Model (Freelance)

| Service | Price | Description |
|---------|-------|-------------|
| **Setup** | €300-500 | Install SelfHostBox, configure domain + SSL |
| **Per app** | €50-100 | Deploy and configure each app |
| **Migration** | €200-500 | Migrate data from cloud services |
| **Monthly maintenance** | €50-150 | Updates, backups, monitoring |
| **Custom app** | €200-500 | Create template for custom app |

## 📄 License

MIT License — use it, sell it, deploy it.

---

Built by [Mounik](https://github.com/Mounik) — DevSecOps Engineer | [SecurePipe](https://github.com/Mounik/SecurePipe) | [HardenLinux](https://github.com/Mounik/HardenLinux) | [InfraWatch](https://github.com/Mounik/InfraWatch) | [docker-stacks](https://github.com/Mounik/docker-stacks) | [devops-toolkit](https://github.com/Mounik/devops-toolkit)