import json
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class DeployedApp(db.Model):
    __tablename__ = "deployed_apps"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    app_type = db.Column(db.String(50), nullable=False)
    domain = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="stopped")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    env_vars = db.Column(db.Text, default="{}")
    volumes = db.Column(db.Text, default="[]")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.app_type,
            "domain": self.domain,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "env_vars": json.loads(self.env_vars) if self.env_vars else {},
            "volumes": json.loads(self.volumes) if self.volumes else [],
        }
