from flask_sqlalchemy import SQLAlchemy
from extensions import db

# ArchiveLog Model
class ArchiveLog(db.Model):
    __tablename__ = "archive_logs"

    log_id = db.Column(db.Integer, primary_key=True)
    plate_number = db.Column(db.String(255), nullable=False)
    username = db.Column(db.String(255), nullable=True)
    identity = db.Column(db.String(255), nullable=True)
    time_in = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime, nullable=True)