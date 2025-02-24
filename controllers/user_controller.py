from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo
from models.user import User
from extensions import db
from models.personal_access_token import PersonalAccessToken
import secrets

manila_tz = ZoneInfo("Asia/Manila")
user_controller = Blueprint("user_controller", __name__)

# User Login
@user_controller.route("/login", methods=["POST"])
def login_user():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message" : "Email does not exist"})
    
    if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        return jsonify({"message": "Incorrect password"})
    
    # Generate a new token
    token = secrets.token_hex(32)
    token_entry = PersonalAccessToken(
        tokenable_type="User",
        tokenable_id=user.id_number,
        name="Personal Access Token",
        token=token,
        abilities="*",
        last_used_at=datetime.now(manila_tz),
        created_at=datetime.now(manila_tz),
        updated_at=datetime.now(manila_tz),
        user_id=user.id_number
    )
    db.session.add(token_entry)
    db.session.commit()

    return jsonify({
        "message": "success",
        "token": token,
        "username": user.username,
        "user_type": user.user_type
    })

# User Logout
@user_controller.route("/logout", methods=["POST"])
def logout_user():
    data = request.get_json()
    token = data.get("token")

    token_entry = PersonalAccessToken.query.filter_by(token=token).first()

    if token_entry:
        db.session.delete(token_entry)
        db.session.commit()
        return jsonify({"message": "token exist"})
    
    return jsonify({"message" : "Invalid token"})

# User Register
@user_controller.route("/user-register", methods=["POST"])
def register_user():
    data = request.get_json()
    id_number = data.get('id_number')
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    user_type = data.get('user_type')
    
    if User.query.filter(User.id_number == id_number).first():
        return jsonify({"message": "id number already used"})
    if User.query.filter(User.username == username).first():
        return jsonify({"message": "username already used"})
    if User.query.filter(User.email == email).first():
        return jsonify({"message": "email already used"}) 

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    user = User(
        id_number=id_number,
        username=username,
        password=hashed_password,
        email=email,
        user_type=user_type
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "success"})

# Fetch all Users
@user_controller.route('/fetch-users', methods=['GET'])
def display_users():
    users = User.query.all()
    user_list = [{
        "id_number": user.id_number,
        "username": user.username,
        "email": user.email,
        "user_type": user.user_type
    } for user in users]

    return jsonify({"userList": user_list})

# Fetch a specific User details
@user_controller.route('/fetch-user/<int:id_number>', methods=['GET'])
def display_user(id_number):
    user = User.query.get(id_number)

    if not user:
        return jsonify({"message": "User not found"})

    user_details = {
        "id_number": user.id_number,
        "username": user.username,
        "email": user.email,
        "user_type": user.user_type
    }

    return jsonify({"userDetails": user_details})

# User update
@user_controller.route('/update-user', methods=['POST'])
def update_user():
    data = request.get_json()
    id_number = data.get('id_number')

    user = User.query.get(id_number)

    if not user:
        return jsonify({"message": "User not found"})

    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    user.password = generate_password_hash(data.get('password')) if 'password' in data else user.password
    user.user_type = data.get('user_type', user.user_type)

    db.session.commit()

    return jsonify({"message": "success"})

#User delete
@user_controller.route('/delete-user', methods=['POST'])
def delete_user():
    data = request.get_json()
    id_number = data.get('id_number')

    user = User.query.get(id_number)

    if not user:
        return jsonify({"message": "User not found"})

    db.session.delete(user)
    db.session.commit()

    return jsonify({"message": "success"})