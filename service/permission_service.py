from config.database import db
from models.permission_model import Permission
from models.asset_model import Asset
from models.audit_model import AuditLog

def grant_permission(asset_id, user_id, permission_type, granted_by=None):
    existing = Permission.query.filter_by(asset_id=asset_id, user_id=user_id).first()
    if existing:
        existing.permission_type = permission_type
        permission = existing
    else:
        permission = Permission(asset_id=asset_id, user_id=user_id, permission_type=permission_type, granted_by=granted_by)
        db.session.add(permission)

    asset = Asset.query.get(asset_id)
    db.session.add(AuditLog(user_id=granted_by, action="GRANT_PERMISSION", details=f"Granted {permission_type} access to user {user_id} for {asset.original_name if asset else asset_id}"))
    db.session.commit()
    return permission

def revoke_permission(permission_id, revoked_by=None):
    permission = Permission.query.get(permission_id)
    if not permission:
        return False
    db.session.add(AuditLog(user_id=revoked_by, action="REVOKE_PERMISSION", details=f"Revoked permission {permission_id}"))
    db.session.delete(permission)
    db.session.commit()
    return True
