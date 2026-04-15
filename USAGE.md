# SelfHostBox - Guide d'utilisation

## 🚀 Installation rapide

### Méthode 1: Script universel (Ubuntu/Debian)

```bash
curl -fsSL https://raw.githubusercontent.com/Mounik/SelfHostBox/main/install-selfhostbox.sh | sudo bash
```

### Méthode 2: VM Proxmox existante

```bash
# Sur la VM
sudo apt-get update
sudo apt-get install -y git docker.io
cd /opt && sudo git clone https://github.com/Mounik/SelfHostBox.git selfhostbox
cd selfhostbox && sudo bash install.sh
```

## 📁 Structure après installation

```
/opt/selfhostbox/
├── backend/          # Code Python Flask
├── frontend/         # Templates HTML
├── config/           # Fichiers de configuration
├── data/             # Données des applications
├── backups/          # Sauvegardes
└── apps/             # Docker Compose files
```

## 🔧 Commandes utiles

| Commande | Description |
|----------|-------------|
| `sudo systemctl status selfhostbox` | Voir le statut du service |
| `sudo systemctl restart selfhostbox` | Redémarrer SelfHostBox |
| `sudo journalctl -u selfhostbox -f` | Voir les logs en temps réel |
| `cd /opt/selfhostbox && sudo docker ps` | Voir les conteneurs Docker |
| `sudo docker compose -f docker-compose.traefik.yml logs -f` | Voir les logs Traefik |

## 🌐 Accès

Une fois installé, accédez à SelfHostBox :
- **URL**: `http://<ip-de-la-vm>:8080`
- **Exemple**: `http://192.168.1.41:8080`

## 🛠️ Dépannage

### Le service ne démarre pas

```bash
# Vérifier les logs
sudo journalctl -u selfhostbox --no-pager | tail -20

# Redémarrer manuellement
sudo systemctl restart selfhostbox
```

### Docker ne fonctionne pas

```bash
# Vérifier Docker
sudo systemctl status docker
sudo systemctl restart docker

# Vérifier les conteneurs
sudo docker ps
```

### Réinstaller proprement

```bash
# Arrêter le service
sudo systemctl stop selfhostbox

# Nettoyer
sudo rm -rf /opt/selfhostbox

# Réinstaller
cd /opt && sudo git clone https://github.com/Mounik/SelfHostBox.git selfhostbox
cd selfhostbox && sudo bash install.sh
```

## 📱 Déployer une application

1. Ouvrez l'interface web: `http://<ip>:8080`
2. Choisissez une application (ex: Vaultwarden)
3. Cliquez sur **"Deploy"**
4. Attendez 30-60 secondes
5. L'application est accessible via son sous-domaine

## 🔒 Sécurité

- Changez le mot de passe root après installation
- Utilisez des domaines personnalisés avec SSL (Let's Encrypt)
- Activez les backups automatiques

---

**Plus d'infos**: https://github.com/Mounik/SelfHostBox
