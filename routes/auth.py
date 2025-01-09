
from flask import jsonify, request, Blueprint
from flask_jwt_extended import create_access_token

from database_config import get_db_connection
from app_config import app, bcrypt, jwt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password_hash FROM users WHERE username = %s;", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.check_password_hash(user[1], password):
        access_token = create_access_token(identity=user[0])
        return jsonify({"access_token": access_token, "user_id": user[0]}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    fullname = data['fullname']
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    # Check if username already exists
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
    existing_user = cursor.fetchone()
    if existing_user:
        cursor.close()
        conn.close()
        return jsonify({"message": "Username already exists"}), 400

    # Check if email already exists
    cursor.execute("SELECT 1 FROM users WHERE email = %s", (email,))
    existing_email = cursor.fetchone()
    if existing_email:
        cursor.close()
        conn.close()
        return jsonify({"message": "Email already exists"}), 400

    # Insert new user into the database
    cursor.execute(
        "INSERT INTO users (username, full_name, email, password_hash) VALUES (%s, %s, %s, %s)",
        (username, fullname, email, password_hash)  # You should hash the password before saving it
    )
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "User registered successfully"}), 201