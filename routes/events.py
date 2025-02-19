import os
import os

import psycopg2
from flask import Blueprint, send_from_directory, abort
from flask import jsonify, request
from database_config import get_db_connection
from app_config import app, bcrypt, jwt
events_bp = Blueprint('events', __name__)

EVENT_UPLOAD_FOLDER = 'uploads/events/'
USER_UPLOAD_FOLDER = 'uploads/users/'
os.makedirs(EVENT_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(USER_UPLOAD_FOLDER, exist_ok=True)

@events_bp.route('/events', methods=['GET'])
def get_events():
    sort_options = request.args.get('sort')
    distance_options = request.args.get('distance')
    filter_options = request.args.get('type', '')
    filter_options = filter_options.split(',')
    print(filter_options)
    conn = get_db_connection()
    cursor = conn.cursor()
    flag = True
    try:
        query_base = "SELECT event_id, events.title, description, " \
                     "lat, lon, address, start_date, end_date, " \
                     "start_time, end_time, events.type_id, event_types.title, created_at, is_allowed, is_canceled" \
                     " FROM events, event_types " \
                     "WHERE events.type_id = event_types.type_id "

        if filter_options[0] != "" and filter_options[0] != "all":
            # cursor.execute(query_base +
            #                f"AND event_types.type_id = {filter_options[0]};")
            query_base +=  f"AND events.type_id in ({",".join(filter_options)}) "
            print("types")
            print(filter_options)
            flag = False

        # TODO: добавить сортировку по расстоянию

        if sort_options == "earlier":
            query_base += f"ORDER BY start_date ASC"
            print("order")
            flag = False

        elif sort_options == "later":
            query_base += f"ORDER BY start_date DESC"
            print("order")
            flag = False


        query_base += ";"

        if not flag:
            print("123")
            cursor.execute(query_base)
        else:
            cursor.execute("SELECT event_id, events.title, description, "
                           "lat, lon, address, start_date, end_date, "
                           "start_time, end_time, events.type_id, event_types.title, created_at, is_allowed, is_canceled"
                           " FROM events, event_types "
                           "WHERE events.type_id = event_types.type_id;")

        events = cursor.fetchall()
        events_data = [
            {
                'event_id': event[0],
                'title': event[1],
                'description': event[2],
                'lat': event[3],
                'lon': event[4],
                'address': event[5],
                'start_date': event[6],
                'end_date': event[7],
                'start_time': str(event[8]),
                'end_time': str(event[9]),
                'type_id': event[10],
                'type_title': str(event[11]),
                'created_at': event[12],
                'is_allowed': event[13],
                'is_canceled': event[14]
            }
            for event in events
        ]
        print(events_data)
        return jsonify(events_data)
    finally:
        conn.close()

@app.route('/events/<int:event_id>/event_image', methods=['GET'])
def get_image(event_id):
    try:
        # Проверяем, существует ли файл
        if os.path.exists(os.path.join("uploads/events", f"{event_id}.jpg")):
            # Отправляем файл
            return send_from_directory("uploads/events", f"{event_id}.jpg")
        else:
            # Если файл не найден, возвращаем 404
            abort(404, description="File not found")
    except Exception as e:
        try:
            # Проверяем, существует ли файл
            if os.path.exists(os.path.join("uploads/users", f"{event_id}.png")):
                # Отправляем файл
                return send_from_directory("uploads/users", f"{event_id}.png")
            else:
                # Если файл не найден, возвращаем 404
                abort(404, description="File not found")
        except Exception as e:
            abort(500, description=f"Server error: {e}")




@events_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # cursor.execute("SELECT event_id, events.title, description, "
        #                "lat, lon, address, start_date, end_date, "
        #                "start_time, end_time, events.type_id,created_at, "
        #                "is_allowed, is_canceled, event_types.title "
        #                "FROM events, event_types "
        #                "WHERE event_id = %s "
        #                "AND events.type_id = event_types.type_id;", (event_id,))
        cursor.execute("""
    SELECT 
        e.event_id,
        e.title,
        e.description,
        e.lat,
        e.lon,
        e.address,
        e.start_date,
        e.end_date,
        e.start_time,
        e.end_time,
        e.picture_url,
        e.type_id,
        et.title AS event_type,  -- Получаем название типа события
        e.created_at,
        e.is_allowed,
        e.is_canceled,
        u.username,
        u.profile_picture_url,
        u.user_id,
        us.title AS status
    FROM events e
    JOIN users u ON e.creator_id = u.user_id
    LEFT JOIN user_statuses us ON u.status_id = us.status_id
    LEFT JOIN event_types et ON e.type_id = et.type_id  -- Соединяем с таблицей event_types
    WHERE e.event_id = %s;
""", (event_id,))
        event = cursor.fetchone()
        if event:
            event_data = {
                'event_id': event[0],
        'title': event[1],
        'description': event[2],
        'lat': event[3],
        'lon': event[4],
        'address': event[5],
        'start_date': event[6],
        'end_date': event[7],
        'start_time': str(event[8]),
        'end_time': str(event[9]),
        'picture_url': event[10],
        'type_id': event[11],
        'event_type': event[12],  # Добавлено поле для типа события
        'created_at': event[13],
        'is_allowed': event[14],
        'is_canceled': event[15],
        'username': event[16],
        'profile_picture_url': event[17],
        'user_id': event[18],
        'status': event[19]
            }
            return jsonify(event_data)
        else:
            return jsonify({'message': 'Event not found'}), 404
    finally:
        conn.close()


@events_bp.route('/events/add', methods=['POST'])
def add_event():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO events (title, description, lat, lon, address, start_date, start_time, end_time, type_id, creator_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING event_id;",
            (data['title'], data['description'], data['lat'], data['lon'], data['address'], data['start_date'], data['start_time'], data['end_time'], data['type_id'], data['creator_id'])
        )
        event_id = cursor.fetchone()[0]
        conn.commit()

        image = request.files['image']
        image_path = os.path.join(EVENT_UPLOAD_FOLDER, str(event_id) + ".jpg")
        image.save(image_path)

        cursor.execute("UPDATE events SET picture_url = %s WHERE event_id = %s;", (image_path, event_id))
        conn.commit()

        return jsonify({'message': 'Event created successfully', 'event_id': event_id}), 201
    finally:
        conn.close()

@events_bp.route('/events/types', methods=['GET'])
def get_event_types():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT  type_id, title FROM event_types;")
        event_types = cursor.fetchall()
        types_data = [
            {
                'type_id': event_type[0],
                'title': event_type[1]
            }
            for event_type in event_types
        ]
        return jsonify(types_data), 200
    finally:
        conn.close()

@events_bp.route('/events/placemarks', methods=['GET'])
def get_placemarks():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""SELECT 
    event_id,
    lat,
    lon,
    et.title
    FROM events e
    LEFT JOIN event_types et ON e.type_id = et.type_id  -- Соединяем с таблицей event_types
    """)
        event_types = cursor.fetchall()
        types_data = [
            {
                'event_id': event_type[0],
                'lat': event_type[1],
                'lon': event_type[2]
            }
            for event_type in event_types
        ]
        return jsonify(types_data), 200
    finally:
        conn.close()




@events_bp.route('/events/<int:event_id>/edit', methods=['PUT'])
def edit_event(event_id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE events SET title = %s, description = %s, lat = %s, lon = %s, address = %s, start_date = %s, end_date = %s, start_time = %s, end_time = %s, type_id = %s, creator_id = %s WHERE event_id = %s;",
            (data['title'], data['description'], data['lat'], data['lon'], data['address'], data['start_date'], data['end_date'], data['start_time'], data['end_time'], data['type_id'], data['creator_id'], event_id)
        )
        conn.commit()
        return jsonify({'message': 'Event updated successfully'})
    finally:
        conn.close()

# удалить мероприятие
@events_bp.route('/events/<int:event_id>/delete', methods=['DELETE'])
def delete_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM events WHERE event_id = %s;", (event_id,))
        conn.commit()
        return jsonify({'message': 'Event deleted successfully'})
    finally:
        conn.close()

# проверить регистрацию пользователя
@events_bp.route('/events/<int:event_id>/check_registration/<int:user_id>', methods=['GET'])
def check_register_for_event(event_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем, существует ли событие и пользователь
    cursor.execute("SELECT event_id FROM events WHERE event_id = %s;", (event_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Event not found'}), 404

    cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'User not found'}), 404

    # Проверяем регистрацию
    cursor.execute("SELECT * FROM event_registrations WHERE user_id = %s AND event_id = %s;", (user_id, event_id))
    registration = cursor.fetchone()
    conn.close()

    if registration:
        return jsonify({'message': 'User already registered for this event'}), 400
    else:
        return jsonify({'message': 'User not registered'}), 200

# отменить регистрацию
@events_bp.route('/events/<int:event_id>/cancel_registration/<int:user_id>', methods=['DELETE'])
def cancel_user_registration(event_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем регистрацию
    cursor.execute("SELECT * FROM event_registrations WHERE event_id = %s AND user_id = %s;", (event_id, user_id))
    registration = cursor.fetchone()

    if not registration:
        conn.close()
        return jsonify({'message': 'Registration not found'}), 404

    # Удаляем регистрацию
    cursor.execute("DELETE FROM event_registrations WHERE event_id = %s AND user_id = %s;", (event_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({'message': 'User registration canceled successfully'}), 200

# зарегистрироваться на мероприятие
@events_bp.route('/events/<int:event_id>/register/<int:user_id>', methods=['POST'])
def register_for_event(event_id, user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем, существует ли событие и пользователь
    cursor.execute("SELECT event_id FROM events WHERE event_id = %s;", (event_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Event not found'}), 404

    cursor.execute("SELECT user_id FROM users WHERE user_id = %s;", (user_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'User not found'}), 404

    # Проверяем, что пользователь еще не зарегистрирован
    cursor.execute("SELECT * FROM event_registrations WHERE user_id = %s AND event_id = %s;", (user_id, event_id))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'User already registered for this event'}), 400

    # Добавляем регистрацию
    cursor.execute("INSERT INTO event_registrations (user_id, event_id) VALUES (%s, %s) RETURNING registration_id;",
                   (user_id, event_id))
    registration_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({'message': 'Registration successful', 'registration_id': registration_id}), 201

# получить зарегистрированных на мероприятие пользователей
@events_bp.route('/events/<int:event_id>/registrations', methods=['GET'])
def get_event_registrations(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем, существует ли событие
    cursor.execute("SELECT event_id FROM events WHERE event_id = %s;", (event_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Event not found'}), 404

    # Получаем регистрации
    cursor.execute(
        "SELECT registration_id, user_id, event_id, attendance_confirmed FROM event_registrations WHERE event_id = %s;",
        (event_id,))
    registrations = cursor.fetchall()
    conn.close()

    registrations_data = [
        {
            'registration_id': reg[0],
            'user_id': reg[1],
            'event_id': reg[2],
            'attendance_confirmed': reg[3]
        }
        for reg in registrations
    ]

    return jsonify(registrations_data)

# отменить регистрацию
@events_bp.route('/registrations/<int:registration_id>/cancel', methods=['DELETE'])
def cancel_registration(registration_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Проверяем регистрацию
    cursor.execute("SELECT * FROM event_registrations WHERE registration_id = %s;", (registration_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Registration not found'}), 404

    # Удаляем регистрацию
    cursor.execute("DELETE FROM event_registrations WHERE registration_id = %s;", (registration_id,))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Registration canceled successfully'})

@app.route('/users/<int:user_id>/current_registrations', methods=['GET'])
def get_user_events(user_id):

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    query = """
    SELECT 
        e.event_id,
        e.title,
        e.description,
        e.start_date,
        e.start_time,
        e.end_date,
        e.end_time,
        e.address,
        e.lat,
        e.lon,
        e.picture_url,
        et.title AS event_type
    FROM 
        event_registrations er
    JOIN 
        events e ON er.event_id = e.event_id
    JOIN 
        event_types et ON e.type_id = et.type_id
    WHERE 
        er.user_id = %s
        AND (e.start_date > CURRENT_DATE 
             OR (e.start_date = CURRENT_DATE AND e.start_time > CURRENT_TIME))
        AND e.is_canceled = FALSE;
    """

    try:
        # Подключение к базе данных
        conn = get_db_connection()
        cur = conn.cursor()

        # Выполнение запроса
        cur.execute(query, (user_id,))
        events = cur.fetchall()

        cur.close()
        conn.close()

        # Возврат результата в формате JSON
        return jsonify({'events': events})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/users/<int:user_id>/attended_events', methods=['GET'])
def get_user_attended_events(user_id):

    if not user_id:
        return jsonify({'error': 'User ID is required'}), 400

    query = """
    SELECT 
        e.event_id,
        e.title,
        e.description,
        e.start_date,
        e.start_time,
        e.end_date,
        e.end_time,
        e.address,
        e.lat,
        e.lon,
        e.picture_url,
        et.title AS event_type
    FROM 
        event_registrations er
    JOIN 
        events e ON er.event_id = e.event_id
    JOIN 
        event_types et ON e.type_id = et.type_id
    WHERE 
        er.user_id = %s
        AND er.attendance_confirmed = TRUE
        AND e.end_date <= CURRENT_DATE;
    """

    try:

        conn = get_db_connection()
        cur = conn.cursor()

        # Выполнение запроса
        cur.execute(query, (user_id,))
        events = cur.fetchall()

        cur.close()
        conn.close()

        # Возврат результата в формате JSON
        return jsonify({'events': events})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
