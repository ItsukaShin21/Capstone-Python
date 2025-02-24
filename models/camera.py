from flask_sqlalchemy import SQLAlchemy
from extensions import db

# Camera Model
class Camera(db.Model):
    __tablename__ = 'cameras'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    camera_name = db.Column(db.String(255), nullable=False)
    rtsp_url = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    camera_type = db.Column(db.String(255), nullable=False)