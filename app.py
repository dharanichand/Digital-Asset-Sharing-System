import os
from flask import Flask
from flask_jwt_extended import JWTManager
from config.config import Config
from config.database import db

jwt = JWTManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)

    from models.user_model import User
    from models.asset_model import Asset
    from models.permission_model import Permission
    from models.audit_model import AuditLog

    from routes.auth_routes import auth_bp
    from routes.asset_routes import asset_bp
    from routes.permission_routes import permission_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(asset_bp)
    app.register_blueprint(permission_bp)

    # Creates tables in PostgreSQL on Render if they do not exist.
    with app.app_context():
        db.create_all()

    return app


# Required for Render start command: gunicorn app:app
app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
