from flask_sqlalchemy import SQLAlchemy
from extensions import db
    
# Vehicle Model
class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    plate_number = db.Column(db.String(255), primary_key=True)
    username = db.Column(db.String(255), nullable=True)
    identity = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=True)
    valid_id_url = db.Column(db.String(255), nullable=True)
    license_doc_url = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=True)

    def as_dict(self):
        return {
            "plate_number": self.plate_number,
            "username": self.username,
            "identity": self.identity,
            "email": self.email,
            "valid_id_url": self.valid_id_url,
            "license_doc_url": self.license_doc_url,
            "status": self.status,
            "created_at": self.created_at,
        }