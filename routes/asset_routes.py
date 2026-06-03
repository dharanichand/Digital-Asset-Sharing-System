import os
from flask import Blueprint, request, redirect, render_template, session, send_from_directory, abort, flash, url_for, current_app
from config.database import db
from models.asset_model import Asset
from models.user_model import User
from models.permission_model import Permission
from models.audit_model import AuditLog
from service.asset_service import save_asset, query_visible_assets, can_access, can_download, record_download, delete_asset, toggle_public, log_action
from service.email_service import send_file_uploaded_email, send_public_link_email
from middleware.auth_middleware import login_required

asset_bp = Blueprint("asset", __name__)

@asset_bp.route("/files")
@login_required
def files(current_user):
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    assets_query = query_visible_assets(current_user)
    if q:
        assets_query = assets_query.filter(Asset.original_name.ilike(f"%{q}%"))
    if category:
        assets_query = assets_query.filter_by(category=category)
    assets = assets_query.order_by(Asset.upload_time.desc()).all()
    users = User.query.filter(User.id != current_user.id).all()
    categories = [r[0] for r in db.session.query(Asset.category).distinct().all() if r[0]]
    permissions = Permission.query.all()
    return render_template("files.html", files=assets, users=users, categories=categories, current_user=current_user, permissions=permissions)

@asset_bp.route("/upload", methods=["POST"])
@login_required
def upload(current_user):
    try:
        asset = save_asset(request.files.get("file"), current_user.id, request.form)
        send_file_uploaded_email(current_user, asset)
        flash("File uploaded successfully", "success")
    except Exception as e:
        flash(str(e), "error")
    return redirect("/dashboard")

@asset_bp.route("/admin")
@login_required
def admin(current_user):
    if current_user.role != "admin":
        return "Access Denied", 403

    users = User.query.order_by(User.created_at.desc()).all()
    assets = Asset.query.filter(Asset.status != "deleted").order_by(Asset.upload_time.desc()).all()
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(50).all()

    return render_template(
        "admin.html",
        current_user=current_user,
        users=users,
        assets=assets,
        logs=logs,
        total_assets=len(assets),
        public_assets=Asset.query.filter_by(is_public=True).count(),
        downloads=sum(asset.download_count for asset in assets),
        users_count=len(users)
    )

@asset_bp.route("/download/<int:asset_id>")
@login_required
def download(current_user, asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if not can_download(current_user, asset):
        abort(403)
    record_download(current_user.id, asset)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], asset.filename, as_attachment=True, download_name=asset.original_name)

@asset_bp.route("/view/<int:asset_id>")
@login_required
def view_file(current_user, asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if not can_access(current_user, asset):
        abort(403)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], asset.filename)

@asset_bp.route("/share/<token>")
def public_share(token):
    asset = Asset.query.filter_by(share_token=token, is_public=True, status="active").first_or_404()
    if asset.is_expired():
        return "This shared link has expired", 410
    return render_template("files.html", files=[asset], users=[], categories=[], current_user=None, permissions=[], public_mode=True)

@asset_bp.route("/public-download/<token>")
def public_download(token):
    asset = Asset.query.filter_by(share_token=token, is_public=True, status="active").first_or_404()
    if asset.is_expired() or not asset.allow_download:
        abort(403)
    record_download(None, asset)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], asset.filename, as_attachment=True, download_name=asset.original_name)

@asset_bp.route("/delete/<int:asset_id>", methods=["POST"])
@login_required
def delete(current_user, asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if not delete_asset(current_user, asset):
        abort(403)
    flash("Asset deleted", "success")
    return redirect("/files")

@asset_bp.route("/toggle-public/<int:asset_id>", methods=["POST"])
@login_required
def toggle_public_route(current_user, asset_id):
    asset = Asset.query.get_or_404(asset_id)
    was_public = asset.is_public
    if not toggle_public(current_user, asset):
        abort(403)
    if not was_public and asset.is_public:
        send_public_link_email(current_user, asset)
    log_action(current_user.id, "TOGGLE_PUBLIC", f"Changed public status for {asset.original_name}")
    return redirect("/files")

@asset_bp.route("/toggle-download/<int:asset_id>", methods=["POST"])
@login_required
def toggle_download(current_user, asset_id):
    asset = Asset.query.get_or_404(asset_id)
    if current_user.role != "admin" and asset.owner_id != current_user.id:
        abort(403)
    asset.allow_download = not asset.allow_download
    db.session.commit()
    log_action(current_user.id, "TOGGLE_DOWNLOAD", f"Changed download access for {asset.original_name}")
    return redirect("/files")
