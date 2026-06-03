import os
import uuid
from datetime import datetime
from flask import current_app, request
from werkzeug.utils import secure_filename
from config.database import db
from models.asset_model import Asset
from models.permission_model import Permission
from models.audit_model import AuditLog
from models.user_model import User

def allowed_file(filename):
    """Allow normal documents, images, archives, and source-code files.

    The old check required a dot in the filename, which blocked files like
    Dockerfile, Makefile, .env, LICENSE, README, etc.
    """
    if not filename:
        return False
    safe_name = secure_filename(filename)
    return bool(safe_name)

def parse_expiry(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None

def log_action(user_id, action, details=""):
    ip = request.remote_addr if request else ""
    db.session.add(AuditLog(user_id=user_id, action=action, details=details, ip_address=ip))
    db.session.commit()

def save_asset(file, owner_id, form=None):
    form = form or {}
    if not file or file.filename == "":
        raise ValueError("No file selected")
    if not allowed_file(file.filename):
        raise ValueError("Invalid file name")

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    safe_original = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_original}"
    upload_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_name)
    file.save(upload_path)

    is_public = True if form.get("is_public") == "on" else False
    allow_download = True if form.get("allow_download") == "on" else False

    asset = Asset(
        filename=unique_name,
        original_name=safe_original,
        owner_id=owner_id,
        category=form.get("category", "General") or "General",
        description=form.get("description", ""),
        file_size=os.path.getsize(upload_path),
        file_type=file.content_type or "unknown",
        expiry_date=parse_expiry(form.get("expiry_date")),
        is_public=is_public,
        allow_download=allow_download,
        share_token=uuid.uuid4().hex if is_public else None
    )
    db.session.add(asset)
    db.session.commit()
    log_action(owner_id, "UPLOAD", f"Uploaded {asset.original_name}")
    return asset

def query_visible_assets(user):
    if user.role == "admin":
        return Asset.query.filter(Asset.status != "deleted")
    permitted_ids = [p.asset_id for p in Permission.query.filter_by(user_id=user.id).all()]
    return Asset.query.filter(
        Asset.status != "deleted",
        db.or_(Asset.owner_id == user.id, Asset.is_public == True, Asset.id.in_(permitted_ids))
    )

def can_access(user, asset):
    if not user or not asset or asset.status == "deleted" or asset.is_expired():
        return False
    if user.role == "admin" or asset.owner_id == user.id or asset.is_public:
        return True
    return Permission.query.filter_by(asset_id=asset.id, user_id=user.id).first() is not None

def can_download(user, asset):
    if not can_access(user, asset) or not asset.allow_download:
        return False
    if user.role == "admin" or asset.owner_id == user.id:
        return True
    perm = Permission.query.filter_by(asset_id=asset.id, user_id=user.id).first()
    return asset.is_public or (perm and perm.permission_type in ["download", "owner"])

def record_download(user_id, asset):
    asset.download_count += 1
    db.session.add(asset)
    db.session.add(AuditLog(user_id=user_id, action="DOWNLOAD", details=f"Downloaded {asset.original_name}"))
    db.session.commit()

def delete_asset(user, asset):
    if user.role != "admin" and asset.owner_id != user.id:
        return False
    asset.status = "deleted"
    db.session.add(asset)
    db.session.add(AuditLog(user_id=user.id, action="DELETE", details=f"Deleted {asset.original_name}"))
    db.session.commit()
    return True

def toggle_public(user, asset):
    if user.role != "admin" and asset.owner_id != user.id:
        return False
    asset.is_public = not asset.is_public
    asset.share_token = uuid.uuid4().hex if asset.is_public and not asset.share_token else asset.share_token
    if not asset.is_public:
        asset.share_token = None
    db.session.commit()
    return True
