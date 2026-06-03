from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config.database import db
from models.user_model import User
from models.audit_model import AuditLog

VALID_ROLES = ["user", "owner", "group_admin"]

def log_auth(user_id, action, details="", ip_address=""):
    db.session.add(AuditLog(user_id=user_id, action=action, details=details, ip_address=ip_address))
    db.session.commit()

def register_user(data):
    role = data.get("role", "user")
    if role not in VALID_ROLES:
        role = "user"
    # Security fix: never auto-create admin during public registration.

    user = User(
        username=data.get("username", "").strip(),
        email=data.get("email", "").strip().lower(),
        password=generate_password_hash(data.get("password", "")),
        role=role,
        group_name=data.get("group_name", "General").strip() or "General"
    )
    db.session.add(user)
    db.session.commit()
    log_auth(user.id, "REGISTER", f"New account created with role {user.role}")
    return user

def authenticate_user(user, password):
    if not user or not user.is_active:
        return False
    return check_password_hash(user.password, password)

def mark_login(user, ip_address=""):
    user.last_login = datetime.utcnow()
    db.session.add(AuditLog(user_id=user.id, action="LOGIN", details="User signed in", ip_address=ip_address))
    db.session.commit()
