from functools import wraps
from flask import session, redirect, jsonify
from models.user_model import User

try:
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
except Exception:
    verify_jwt_in_request = None
    get_jwt_identity = None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/login")
        user = User.query.get(session["user_id"])
        if not user or not user.is_active:
            session.clear()
            return redirect("/login")
        return f(user, *args, **kwargs)
    return wrapper

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return "Access Denied", 403
            return f(current_user, *args, **kwargs)
        return wrapper
    return decorator

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            current_user = get_jwt_identity()
        except Exception:
            return jsonify({"message": "Token missing or invalid"}), 401
        return f(current_user, *args, **kwargs)
    return wrapper
