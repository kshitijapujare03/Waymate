from werkzeug.security import generate_password_hash, check_password_hash
from db import get_db_connection


def create_user(full_name, email, password):
    connection = get_db_connection()
    cursor = connection.cursor()

    password_hash = generate_password_hash(password)

    query = """
        INSERT INTO users (full_name, email, password_hash)
        VALUES (%s, %s, %s)
    """

    cursor.execute(query, (full_name, email, password_hash))

    connection.commit()

    user_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return user_id


def verify_user(email, password):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT id, full_name, email, password_hash
        FROM users
        WHERE email = %s
    """

    cursor.execute(query, (email,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user and check_password_hash(user["password_hash"], password):
        return user

    return None