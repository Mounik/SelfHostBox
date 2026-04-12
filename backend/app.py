"""SelfHostBox — Web UI for self-hosted apps"""

import os
import json
import subprocess
import secrets
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import yaml

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////opt/selfhostbox/selfhostbox.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

APPS_DIR = Path('/opt/selfhostbox/apps')
TEMPLATES_DIR = Path(__file__).parent / 'templates' / 'apps'

class DeployedApp(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    app_type = db.Column(db.String(50), nullable=False)
    domain = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='stopped')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    env_vars = db.Column(db.Text, default='{}')
    volumes = db.Column(db.Text, default='[]')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.app_type,
            'domain': self.domain,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'env_vars': json.loads(self.env_vars),
            'volumes': json.loads(self.volumes)
        }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/apps')
def list_apps():
    apps = DeployedApp.query.all()
    return jsonify([a.to_dict() for a in apps])

@app.route('/api/apps', methods=['POST'])
def deploy_app():
    data = request.json
    app_type = data['app_type']
    name = data.get('name', f"{app_type}-{secrets.token_hex(4)}")
    domain = data.get('domain', f"{name}.selfhostbox.local")
    
    # Load template
    template_path = TEMPLATES_DIR / app_type / 'docker-compose.yml'
    if not template_path.exists():
        return jsonify({'error': f'Template {app_type} not found'}), 404
    
    # Prepare app directory
    app_dir = APPS_DIR / name
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Render compose file
    with open(template_path) as f:
        compose = f.read()
    
    compose = compose.replace('${APP_NAME}', name)
    compose = compose.replace('${DOMAIN}', domain)
    
    # Add environment variables
    env_vars = data.get('env_vars', {})
    for key, value in env_vars.items():
        compose = compose.replace(f'${{{key}}}', str(value))
    
    # Write compose file
    with open(app_dir / 'docker-compose.yml', 'w') as f:
        f.write(compose)
    
    # Deploy
    result = subprocess.run(
        ['docker-compose', 'up', '-d'],
        cwd=app_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        app = DeployedApp(
            name=name,
            app_type=app_type,
            domain=domain,
            status='running',
            env_vars=json.dumps(env_vars),
            volumes=json.dumps([])
        )
        db.session.add(app)
        db.session.commit()
        return jsonify(app.to_dict()), 201
    else:
        return jsonify({'error': result.stderr}), 500

@app.route('/api/apps/<int:app_id>/start', methods=['POST'])
def start_app(app_id):
    app = DeployedApp.query.get_or_404(app_id)
    app_dir = APPS_DIR / app.name
    subprocess.run(['docker-compose', 'start'], cwd=app_dir)
    app.status = 'running'
    db.session.commit()
    return jsonify(app.to_dict())

@app.route('/api/apps/<int:app_id>/stop', methods=['POST'])
def stop_app(app_id):
    app = DeployedApp.query.get_or_404(app_id)
    app_dir = APPS_DIR / app.name
    subprocess.run(['docker-compose', 'stop'], cwd=app_dir)
    app.status = 'stopped'
    db.session.commit()
    return jsonify(app.to_dict())

@app.route('/api/apps/<int:app_id>', methods=['DELETE'])
def delete_app(app_id):
    app = DeployedApp.query.get_or_404(app_id)
    app_dir = APPS_DIR / app.name
    subprocess.run(['docker-compose', 'down', '-v'], cwd=app_dir)
    import shutil
    shutil.rmtree(app_dir, ignore_errors=True)
    db.session.delete(app)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route('/api/store')
def list_store():
    """List available app templates."""
    apps = []
    for template_dir in TEMPLATES_DIR.iterdir():
        if template_dir.is_dir():
            manifest_path = template_dir / 'manifest.json'
            if manifest_path.exists():
                with open(manifest_path) as f:
                    apps.append(json.load(f))
            else:
                apps.append({
                    'name': template_dir.name.title(),
                    'id': template_dir.name,
                    'description': f'{template_dir.name} self-hosted app',
                    'category': 'misc'
                })
    return jsonify(apps)

@app.route('/api/system/info')
def system_info():
    import psutil
    return jsonify({
        'cpu_percent': psutil.cpu_percent(),
        'memory': {
            'total': psutil.virtual_memory().total,
            'available': psutil.virtual_memory().available,
            'percent': psutil.virtual_memory().percent
        },
        'disk': {
            'total': psutil.disk_usage('/').total,
            'free': psutil.disk_usage('/').free,
            'percent': psutil.disk_usage('/').percent
        }
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)