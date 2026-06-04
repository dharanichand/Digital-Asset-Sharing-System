from flask import Blueprint, request, render_template, redirect, session, flash, current_app
from config.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from models.user_model import User
from models.asset_model import Asset
from models.audit_model import AuditLog
from service.auth_service import register_user, authenticate_user, mark_login, log_auth
from service.email_service import send_welcome_email, send_password_reset_email
from middleware.auth_middleware import login_required

auth_bp = Blueprint("auth", __name__)

def _password_reset_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

def _make_password_reset_token(user):
    return _password_reset_serializer().dumps(user.email, salt="password-reset")

def _read_password_reset_token(token):
    max_age = current_app.config.get("PASSWORD_RESET_TOKEN_MAX_AGE", 1800)
    return _password_reset_serializer().loads(token, salt="password-reset", max_age=max_age)


@auth_bp.route("/")
def index():
    if "user_id" in session:
        return redirect("/dashboard")
    return render_template("index.html")

@auth_bp.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.form
    if not data.get("username") or not data.get("email") or not data.get("password"):
        flash("All fields are required", "error")
        return redirect("/register")
    existing = User.query.filter_by(email=data["email"].strip().lower()).first()
    if existing:
        flash("User already exists", "error")
        return redirect("/register")
    user = register_user(data)
    send_welcome_email(user)
    flash("Account created successfully. Please log in.", "success")
    return redirect("/login")

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.form
    user = User.query.filter_by(email=data.get("email", "").strip().lower()).first()
    if user and authenticate_user(user, data.get("password", "")):
        session["user_id"] = user.id
        session["username"] = user.username
        session["role"] = user.role
        mark_login(user, request.remote_addr)
        return redirect("/dashboard")
    flash("Invalid credentials", "error")
    return redirect("/login")

@auth_bp.route("/logout")
def logout():
    uid = session.get("user_id")
    if uid:
        log_auth(uid, "LOGOUT", "User signed out", request.remote_addr)
    session.clear()
    return redirect("/login")


@auth_bp.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    return render_template("forgot_password.html")

@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    email = request.form.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()

    # Do not reveal whether the email exists. This is safer for real apps.
    if user:
        token = _make_password_reset_token(user)
        sent = send_password_reset_email(user, token)
        if not sent:
            current_app.logger.error("Password reset email was not sent. Check MAIL_* environment variables in Render.")
            flash("Password reset email could not be sent right now. Please check mail configuration.", "error")
            return redirect("/forgot-password")

    flash("If that email exists, a password reset link has been sent.", "success")
    return redirect("/forgot-password")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = _read_password_reset_token(token)
    except SignatureExpired:
        flash("Password reset link expired. Please request a new one.", "error")
        return redirect("/forgot-password")
    except BadSignature:
        flash("Invalid password reset link.", "error")
        return redirect("/forgot-password")

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid password reset link.", "error")
        return redirect("/forgot-password")

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return redirect(f"/reset-password/{token}")

        if confirm_password and password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(f"/reset-password/{token}")

        user.password = generate_password_hash(password)
        db.session.commit()
        log_auth(user.id, "PASSWORD_RESET", "Password reset completed", request.remote_addr)
        flash("Password updated successfully. Please log in.", "success")
        return redirect("/login")

    return render_template("reset_password.html")

@auth_bp.route("/dashboard")
@login_required
def dashboard(current_user):
    if current_user.role == "admin":
        asset_query = Asset.query.filter(Asset.status != "deleted")
        log_query = AuditLog.query
        users_count = User.query.count()
    else:
        asset_query = Asset.query.filter(Asset.status != "deleted", Asset.owner_id == current_user.id)
        log_query = AuditLog.query.filter_by(user_id=current_user.id)
        users_count = 1

    total_assets = asset_query.count()
    public_assets = asset_query.filter(Asset.is_public == True).count()
    downloads = db.session.query(db.func.sum(Asset.download_count)).filter(Asset.status != "deleted").scalar() or 0

    if current_user.role != "admin":
        downloads = db.session.query(db.func.sum(Asset.download_count)).filter(
            Asset.status != "deleted",
            Asset.owner_id == current_user.id
        ).scalar() or 0

    recent_assets = asset_query.order_by(Asset.upload_time.desc()).limit(6).all()
    recent_logs = log_query.order_by(AuditLog.timestamp.desc()).limit(8).all()

    return render_template(
        "dashboard.html",
        current_user=current_user,
        total_assets=total_assets,
        public_assets=public_assets,
        downloads=downloads,
        users_count=users_count,
        recent_assets=recent_assets,
        recent_logs=recent_logs
    )

@auth_bp.route("/profile", methods=["GET"])
@login_required
def profile(current_user):
    return render_template("profile.html", current_user=current_user)

@auth_bp.route("/profile", methods=["POST"])
@login_required
def update_profile(current_user):
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not username or not email:
        flash("Username and email are required.", "error")
        return redirect("/profile")

    existing = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing:
        flash("That email is already used by another account.", "error")
        return redirect("/profile")

    current_user.username = username
    current_user.email = email
    db.session.commit()
    session["username"] = current_user.username
    flash("Profile updated successfully.", "success")
    return redirect("/profile")

@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password(current_user):
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not check_password_hash(current_user.password, current_password):
        flash("Current password is incorrect.", "error")
        return redirect("/profile")

    if len(new_password) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect("/profile")

    if new_password != confirm_password:
        flash("New password and confirm password do not match.", "error")
        return redirect("/profile")

    current_user.password = generate_password_hash(new_password)
    db.session.commit()
    flash("Password changed successfully.", "success")
    return redirect("/profile")

@auth_bp.route("/admin/user/<int:user_id>/role", methods=["POST"])
@login_required
def change_role(current_user, user_id):
    if current_user.role != "admin":
        return "Access Denied", 403
    user = User.query.get_or_404(user_id)
    user.role = request.form.get("role", user.role)
    db.session.commit()
    return redirect("/admin")
