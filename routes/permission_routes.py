from flask import Blueprint, request, redirect, abort, flash
from models.asset_model import Asset
from models.permission_model import Permission
from models.user_model import User
from service.permission_service import grant_permission, revoke_permission
from service.email_service import send_permission_granted_email
from middleware.auth_middleware import login_required

permission_bp = Blueprint("permission", __name__)

@permission_bp.route("/grant", methods=["POST"])
@login_required
def grant(current_user):
    asset = Asset.query.get_or_404(int(request.form["asset_id"]))
    if current_user.role != "admin" and asset.owner_id != current_user.id:
        abort(403)
    target_user_id = int(request.form["user_id"])
    permission_type = request.form.get("permission_type", "view")
    grant_permission(asset.id, target_user_id, permission_type, current_user.id)
    target_user = User.query.get(target_user_id)
    if target_user:
        send_permission_granted_email(target_user, current_user, asset, permission_type)
    flash("Permission granted", "success")
    return redirect("/files")

@permission_bp.route("/revoke/<int:permission_id>", methods=["POST"])
@login_required
def revoke(current_user, permission_id):
    permission = Permission.query.get_or_404(permission_id)
    asset = Asset.query.get_or_404(permission.asset_id)
    if current_user.role != "admin" and asset.owner_id != current_user.id:
        abort(403)
    revoke_permission(permission_id, current_user.id)
    flash("Permission revoked", "success")
    return redirect("/files")
