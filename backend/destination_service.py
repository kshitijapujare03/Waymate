from db import get_db_connection


def get_popular_destinations(user_id=None):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # -------------------------------------------------
    # If there is no logged-in user:
    # Return 4 random destinations.
    # -------------------------------------------------

    if not user_id:

        query = """
            SELECT
                id,
                name,
                location,
                destination_type,
                description,
                budget_min,
                budget_max,
                weather,
                packing_essentials,
                rating,
                image_url
            FROM destinations
            WHERE is_popular = 1
            ORDER BY rating DESC, id ASC
            LIMIT 10
        """

        cursor.execute(query)

        destinations = cursor.fetchall()

        cursor.close()
        connection.close()

        return destinations

        cursor.execute(query)

        destinations = cursor.fetchall()

        cursor.close()
        connection.close()

        return destinations

    # -------------------------------------------------
    # If user is logged in:
    # Select destinations based on user interaction.
    #
    # Search      = 1 point
    # Saved       = 2 points
    # Trip        = 3 points
    # -------------------------------------------------

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
            d.image_url,

            (
                (
                    SELECT COUNT(*)
                    FROM search_history sh
                    WHERE sh.user_id = %s
                    AND (
                        LOWER(sh.search_query)
                        LIKE CONCAT('%%', LOWER(d.name), '%%')

                        OR

                        LOWER(d.name)
                        LIKE CONCAT('%%', LOWER(sh.search_query), '%%')

                        OR

                        LOWER(sh.search_query)
                        LIKE CONCAT(
                            '%%',
                            LOWER(d.destination_type),
                            '%%'
                        )
                    )
                ) * 1

                +

                (
                    SELECT COUNT(*)
                    FROM saved_places sp
                    WHERE sp.user_id = %s
                    AND sp.destination_id = d.id
                ) * 2

                +

                (
                    SELECT COUNT(*)
                    FROM trips t
                    WHERE t.user_id = %s
                    AND t.destination_id = d.id
                ) * 3

            ) AS interaction_score

        FROM destinations d

        ORDER BY
            interaction_score DESC,
            RAND()

        LIMIT 4
    """

    cursor.execute(
        query,
        (
            user_id,
            user_id,
            user_id
        )
    )

    destinations = cursor.fetchall()

    cursor.close()
    connection.close()

    return destinations


def get_destination(destination_id):
    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            name,
            location,
            destination_type,
            description,
            budget_min,
            budget_max,
            weather,
            packing_essentials,
            rating,
            image_url
        FROM destinations
        WHERE id = %s
    """

    cursor.execute(query, (destination_id,))

    destination = cursor.fetchone()

    if destination:
        spot_query = """
            SELECT
                id,
                spot_name,
                description,
                image_url
            FROM destination_spots
            WHERE destination_id = %s
        """

        cursor.execute(spot_query, (destination_id,))

        destination["spots"] = cursor.fetchall()

    cursor.close()
    connection.close()

    return destination


def search_destinations(search_query):
    connection = get_db_connection()

    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            name,
            location,
            destination_type,
            description,
            budget_min,
            budget_max,
            weather,
            packing_essentials,
            rating,
            image_url
        FROM destinations
        WHERE
            name LIKE %s
            OR location LIKE %s
            OR destination_type LIKE %s
        ORDER BY rating DESC
    """

    search_value = f"%{search_query}%"

    cursor.execute(
        query,
        (search_value, search_value, search_value)
    )

    destinations = cursor.fetchall()

    cursor.close()
    connection.close()

    return destinations

def get_all_destinations():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM destinations
    """

    cursor.execute(query)
    destinations = cursor.fetchall()

    cursor.close()
    connection.close()

    return destinations


def get_destination_by_id(destination_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM destinations
        WHERE id = %s
    """

    cursor.execute(query, (destination_id,))
    destination = cursor.fetchone()

    cursor.close()
    connection.close()

    return destination


def get_destination_spots(destination_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT *
        FROM destination_spots
        WHERE destination_id = %s
    """

    cursor.execute(query, (destination_id,))
    spots = cursor.fetchall()

    cursor.close()
    connection.close()

    return spots