from models.user import User
from models.personal_access_token import PersonalAccessToken
import bcrypt
from extensions import db
from flask import Flask

def seed_user():
    app = Flask(__name__)
    # app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://root:@127.0.0.1:3306/capstone_db"
    app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql://admin:admin2102@capstone-db.cnwm0qomkcut.ap-southeast-1.rds.amazonaws.com:3306/capstone-db"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        password = b"admin2102"
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

        new_user = User(
            id_number=1234567,
            username='admin',
            email='admin@gmail.com',
            password=hashed_password,
            user_type='Admin'
        )
        db.session.add(new_user)
        db.session.commit()
        print("Admin user created successfully.")

if __name__ == "__main__":
    seed_user()