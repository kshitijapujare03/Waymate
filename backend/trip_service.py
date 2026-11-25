from db import get_db_connection


def create_trip(
    user_id,
    destination_id,
    trip_type,
    number_of_people,
    number_of_days,
    budget,
    start_date,
    end_date,
    notes=None
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Prevent duplicate upcoming trips for the same user
        # and destination.
        cursor.execute(
            """
            SELECT id
            FROM trips
            WHERE user_id = %s
              AND destination_id = %s
              AND status = 'upcoming'
            ORDER BY id DESC
            LIMIT 1
            """,
            (user_id, destination_id)
        )

        existing_trip = cursor.fetchone()

        if existing_trip:
            connection.commit()
            return existing_trip[0], True

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
                end_date,
                notes
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                end_date,
                notes
            )
        )

        connection.commit()

        return cursor.lastrowid, False

    finally:
        cursor.close()
        connection.close()


def get_user_trips(user_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
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
                t.notes,
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

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


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

    try:
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

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()


def update_trip(
    trip_id,
    user_id,
    start_date,
    end_date,
    number_of_days,
    budget,
    notes,
    status
):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE trips
            SET
                start_date = %s,
                end_date = %s,
                number_of_days = %s,
                budget = %s,
                notes = %s,
                status = %s
            WHERE id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (
                start_date,
                end_date,
                number_of_days,
                budget,
                notes,
                status,
                trip_id,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount

    finally:
        cursor.close()
        connection.close()


def update_trip_status(trip_id, user_id, status):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE trips
            SET status = %s
            WHERE id = %s
            AND user_id = %s
        """

        cursor.execute(
            query,
            (status, trip_id, user_id)
        )

        connection.commit()

        return cursor.rowcount

    finally:
        cursor.close()
        connection.close()


def delete_trip(trip_id, user_id):
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        query = """
            DELETE FROM trips
            WHERE id = %s
              AND user_id = %s
              AND status = 'upcoming'
        """

        cursor.execute(
            query,
            (trip_id, user_id)
        )

        connection.commit()

        return cursor.rowcount

    finally:
        cursor.close()
        connection.close()