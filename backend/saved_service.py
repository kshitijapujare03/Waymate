from db import get_db_connection


def save_place(user_id, destination_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO saved_places
        (user_id, destination_id)
        VALUES (%s, %s)
    """

    cursor.execute(query, (user_id, destination_id))

    connection.commit()

    cursor.close()
    connection.close()


def remove_saved_place(user_id, destination_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        DELETE FROM saved_places
        WHERE user_id = %s
        AND destination_id = %s
    """

    cursor.execute(query, (user_id, destination_id))

    connection.commit()

    cursor.close()
    connection.close()


def get_saved_places(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            d.id,
            d.name,
            d.location,
            d.destination_type,
            d.description,
            d.budget_min,
            d.budget_max,
            d.weather,
            d.packing_essentials,
            d.rating,
            d.image_url
        FROM saved_places s
        JOIN destinations d
            ON s.destination_id = d.id
        WHERE s.user_id = %s
        ORDER BY s.saved_at DESC
    """

    cursor.execute(query, (user_id,))

    destinations = cursor.fetchall()

    cursor.close()
    connection.close()

    return destinations