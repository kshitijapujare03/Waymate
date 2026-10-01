from db import get_db_connection


def create_trip(
    user_id,
    destination_id,
    trip_type,
    number_of_people,
    number_of_days,
    budget,
    start_date,
    end_date
):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO trips
        (
            user_id,
            destination_id,
            trip_type,
            number_of_people,
            number_of_days,
            budget,
            start_date,
            end_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            user_id,
            destination_id,
            trip_type,
            number_of_people,
            number_of_days,
            budget,
            start_date,
            end_date
        )
    )

    connection.commit()

    trip_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return trip_id


def get_user_trips(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            t.id,
            t.trip_type,
            t.number_of_people,
            t.number_of_days,
            t.budget,
            t.start_date,
            t.end_date,
            t.status,

            d.id AS destination_id,
            d.name AS destination_name,
            d.location,
            d.image_url

        FROM trips t

        JOIN destinations d
            ON t.destination_id = d.id

        WHERE t.user_id = %s

        ORDER BY t.start_date DESC
    """

    cursor.execute(query, (user_id,))

    trips = cursor.fetchall()

    cursor.close()
    connection.close()

    return trips


def save_trip_preferences(
    user_id,
    destination_type,
    budget,
    travel_type,
    number_of_people,
    number_of_days,
    start_date
):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO trip_preferences
        (
            user_id,
            destination_type,
            budget,
            travel_type,
            number_of_people,
            number_of_days,
            start_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(
        query,
        (
            user_id,
            destination_type,
            budget,
            travel_type,
            number_of_people,
            number_of_days,
            start_date
        )
    )

    connection.commit()

    preference_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return preference_id