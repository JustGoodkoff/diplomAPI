import os

from flask import Flask, jsonify, request
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager

from routes.events import events_bp
from routes.auth import auth_bp

from database_config import get_db_connection
from flask import Flask, send_from_directory, abort
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

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    user_query = """
    SELECT 
        u.user_id,
        u.username,
        u.email,
        u.full_name,
        u.points,
        us.title AS status
    FROM 
        users u
    LEFT JOIN 
        user_statuses us ON u.status_id = us.status_id
    WHERE 
        u.user_id = %s;
    """

    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(user_query, (user_id,))
        user_data = cur.fetchone()

        data = {
            "user_id": user_data[0],
            "username": user_data[1],
            "email": user_data[2],
            "full_name": user_data[3],
            "points": user_data[4],
            "status": user_data[5]
        }

        print(data)

        cur.close()
        conn.close()

        if not data:
            return jsonify({'error': 'User not found'}), 404


        return jsonify(data)

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/users/<int:user_id>/profile_image', methods=['GET'])
def get_photo(user_id):
    try:
        # Проверяем, существует ли файл
        if os.path.exists(os.path.join("uploads", f"{user_id}.jpg")):
            # Отправляем файл
            return send_from_directory("uploads", f"{user_id}.jpg")
        else:
            # Если файл не найден, возвращаем 404
            abort(404, description="File not found")
    except Exception as e:
        abort(500, description=f"Server error: {e}")


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
