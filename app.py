import os

from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from routes.events import events_bp
from routes.auth import auth_bp

from database_config import get_db_connection

from app_config import app, bcrypt, jwt

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.register_blueprint(auth_bp)
app.register_blueprint(events_bp)




@app.route('/', methods=['GET'])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, email, full_name, profile_picture_url, created_at FROM users;")
    users = cursor.fetchall()
    conn.close()

    users_data = [
        {
            'user_id': user[0],
            'username': user[1],
            'email': user[2],
            'full_name': user[3],
            'profile_picture': user[4],
            'created_at': user[5]
        }
        for user in users
    ]
    return jsonify(users_data)

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    ""

    # cursor.execute("SELECT user_id, username, email, full_name, profile_picture, created_at FROM users WHERE user_id = %s;", (user_id,))
    cursor.execute("""select u.user_id, u.username, u.email, u.full_name, u.profile_picture, us.title from users as u, user_statuses as us
                        where u.user_id = %s
                        and us.status_id = u.status_id""", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_data = {
            'user_id': user[0],
            'username': user[1],
            'email': user[2],
            'full_name': user[3],
            'profile_picture': user[4],
            'status': user[5]
        }
        return jsonify(user_data)
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/users/add', methods=['POST'])
def add_user():
    data = request.get_json()
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, email, password_hash, full_name, profile_picture) VALUES (%s, %s, %s, %s, %s) RETURNING user_id;",
                   (data['username'], data['email'], password_hash, data['full_name'], data.get('profile_picture')))
    user_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({'message': 'User created successfully', 'user_id': user_id}), 201

@app.route('/users/<int:user_id>/edit', methods=['PUT'])
def edit_user(user_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET username = %s, email = %s, password_hash = %s, full_name = %s, profile_picture = %s WHERE user_id = %s;",
        (data['username'], data['email'], bcrypt.generate_password_hash(data['password']).decode('utf-8'), data['full_name'], data.get('profile_picture'), user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User updated successfully'})

@app.route('/users/<int:user_id>/delete', methods=['DELETE'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User deleted successfully'})


if __name__ == "__main__":
    app.run(debug=True)
