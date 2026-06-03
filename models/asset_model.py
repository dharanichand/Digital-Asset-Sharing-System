from datetime import datetime
from config.database import db

class Asset(db.Model):
    __tablename__ = "assets"

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(100), default="General")
    description = db.Column(db.Text, default="")
    file_size = db.Column(db.Integer, default=0)
    file_type = db.Column(db.String(120), default="unknown")
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime, nullable=True)
    is_public = db.Column(db.Boolean, default=False)
    allow_download = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(80), unique=True, index=True, nullable=True)
    download_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="active")  # active, expired, deleted

    owner = db.relationship("User", backref="assets")

    def is_expired(self):
        return self.expiry_date is not None and datetime.utcnow() > self.expiry_date
