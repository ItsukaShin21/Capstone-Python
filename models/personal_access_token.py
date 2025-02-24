from flask_sqlalchemy import SQLAlchemy
from extensions import db

# PersonalAccessToken Model
class PersonalAccessToken(db.Model):
    __tablename__ = 'personal_access_tokens'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer)
    tokenable_type = db.Column(db.String(255), nullable=False)
    tokenable_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    abilities = db.Column(db.Text, nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id_number'), nullable=False)
    user = db.relationship('User', back_populates='personal_access_tokens')