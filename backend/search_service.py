from db import get_db_connection


def save_search(user_id, search_query, destination_id=None):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO search_history
        (user_id, search_query, destination_id)
        VALUES (%s, %s, %s)
    """

    cursor.execute(
        query,
        (user_id, search_query, destination_id)
    )

    connection.commit()

    cursor.close()
    connection.close()


def get_search_history(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            search_query,
            destination_id,
            searched_at
        FROM search_history
        WHERE user_id = %s
        ORDER BY searched_at DESC
    """

    cursor.execute(query, (user_id,))

    history = cursor.fetchall()

    cursor.close()
    connection.close()

    return history