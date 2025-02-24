from flask_sqlalchemy import SQLAlchemy
from extensions import db

# User Model
class User(db.Model):
    __tablename__ = 'users'

    id_number = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)

    personal_access_tokens = db.relationship('PersonalAccessToken', back_populates='user')
    
    def __repr__(self):
        return f"<User {self.username}>"