from datetime import datetime
from config.database import db

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="user", nullable=False)  # user, owner, group_admin, admin
    group_name = db.Column(db.String(120), default="General")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    def is_admin(self):
        return self.role == "admin"

    def can_manage_assets(self):
        return self.role in ["admin", "owner", "group_admin"]
