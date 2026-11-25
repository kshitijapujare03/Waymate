from flask import Flask, request, jsonify
from flask_cors import CORS
from recommendation_service import get_recommendations
import mysql.connector

from db import get_db_connection

from auth_service import (
    create_user,
    verify_user,
    get_user_profile,
    update_user_profile
)

from destination_service import (
    get_popular_destinations,
    get_destination,
    search_destinations,
    get_all_destinations,
    get_destination_by_id,
    get_destination_spots
)

from saved_service import (
    save_place,
    remove_saved_place,
    get_saved_places
)

from search_service import (
    save_search,
    get_search_history
)

from trip_service import (
    create_trip,
    get_user_trips,
    save_trip_preferences
)

from weather_service import get_destination_weather

app = Flask(__name__)

CORS(app)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "message": "Waymate backend is running"
    }), 200


# ============================================================
# REGISTER
# ============================================================

@app.route("/api/register", methods=["POST"])
def register():

    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name or not email or not password:

        return jsonify({
            "message": "Full name, email and password are required"
        }), 400

    try:

        user_id = create_user(
            full_name,
            email,
            password
        )

        return jsonify({
            "message": "Account created successfully",
            "user_id": user_id
        }), 201

    except mysql.connector.IntegrityError:

        return jsonify({
            "message": "An account with this email already exists"
        }), 409

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# LOGIN
# ============================================================

@app.route("/api/login", methods=["POST"])
def login():

    data = request.get_json(silent=True) or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:

        return jsonify({
            "message": "Email and password are required"
        }), 400

    try:

        user = verify_user(
            email,
            password
        )

        if not user:

            return jsonify({
                "message": "Invalid email or password"
            }), 401

        return jsonify({

            "message": "Login successful",

            "user": {
                "id": user["id"],
                "full_name": user["full_name"],
                "email": user["email"]
            }

        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

# ============================================================
# GET USER PROFILE
# ============================================================

@app.route("/api/profile/<int:user_id>", methods=["GET"])
def user_profile(user_id):

    try:
        profile = get_user_profile(user_id)

        if not profile:
            return jsonify({
                "message": "User profile not found"
            }), 404

        return jsonify({
            "profile": profile
        }), 200

    except Exception as e:
        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# UPDATE USER PROFILE
# ============================================================

@app.route("/api/profile/<int:user_id>", methods=["PUT"])
def edit_user_profile(user_id):

    data = request.get_json(silent=True) or {}

    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    mobile_number = (data.get("mobile_number") or "").strip()

    if not full_name or not email:
        return jsonify({
            "message": "Name and email are required"
        }), 400

    if "@" not in email:
        return jsonify({
            "message": "Please enter a valid email address"
        }), 400

    if len(mobile_number) > 15:
        return jsonify({
            "message": "Mobile number cannot exceed 15 characters"
        }), 400

    try:
        update_user_profile(
            user_id,
            full_name,
            email,
            mobile_number or None
        )

        # Fetch the updated profile to confirm the user exists.
        profile = get_user_profile(user_id)

        if not profile:
            return jsonify({
                "message": "User profile not found"
            }), 404

        return jsonify({
            "message": "Profile updated successfully",
            "profile": profile
        }), 200

    except mysql.connector.IntegrityError:
        return jsonify({
            "message": "This email address is already registered"
        }), 409

    except Exception as e:
        return jsonify({
            "message": str(e)
        }), 500

# ============================================================
# POPULAR DESTINATIONS
#
# IMPORTANT:
# Popularity is calculated collectively from ALL interactions.
#
# It is NOT based on the currently logged-in user.
#
# Therefore every user sees the same popular destinations.
# ============================================================

@app.route("/api/destinations/popular", methods=["GET"])
def popular_destinations():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                d.*,
                COUNT(di.id) AS interaction_count

            FROM destinations d

            LEFT JOIN destination_interactions di
                ON d.id = di.destination_id

            GROUP BY d.id

            ORDER BY
                interaction_count DESC,
                d.id ASC

            LIMIT 6
        """

        cursor.execute(query)

        destinations = cursor.fetchall()

        return jsonify({
            "destinations": destinations
        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# POPULAR DESTINATIONS - ALTERNATE URL
#
# This is included so your frontend can use either:
#
# /api/destinations/popular
#
# OR
#
# /api/popular-destinations
# ============================================================

@app.route("/api/popular-destinations", methods=["GET"])
def popular_destinations_old_url():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                d.*,
                COUNT(di.id) AS interaction_count

            FROM destinations d

            LEFT JOIN destination_interactions di
                ON d.id = di.destination_id

            GROUP BY d.id

            ORDER BY
                interaction_count DESC,
                d.id ASC

            LIMIT 6
        """

        cursor.execute(query)

        destinations = cursor.fetchall()

        return jsonify(
            destinations
        ), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# RECORD DESTINATION INTERACTION
#
# MAIN ROUTE
#
# Example:
#
# POST
# /api/destinations/1/interaction
#
# Body:
#
# {
#     "interaction_type": "click"
# }
# ============================================================

@app.route(
    "/api/destinations/<int:destination_id>/interaction",
    methods=["POST"]
)
def record_destination_interaction(destination_id):

    connection = None
    cursor = None

    try:

        data = request.get_json(
            silent=True
        ) or {}

        interaction_type = data.get(
            "interaction_type",
            "click"
        )

        connection = get_db_connection()

        cursor = connection.cursor()

        # First check whether the destination exists.

        cursor.execute(
            """
            SELECT id
            FROM destinations
            WHERE id = %s
            """,
            (destination_id,)
        )

        destination = cursor.fetchone()

        if not destination:

            return jsonify({
                "success": False,
                "error": "Destination not found"
            }), 404

        # Save interaction.

        cursor.execute(
            """
            INSERT INTO destination_interactions
            (
                destination_id,
                interaction_type
            )
            VALUES (%s, %s)
            """,
            (
                destination_id,
                interaction_type
            )
        )

        connection.commit()

        return jsonify({

            "success": True,

            "message": "Interaction recorded",

            "destination_id": destination_id,

            "interaction_type": interaction_type

        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GENERIC INTERACTION ROUTE
#
# This is included for compatibility with frontend code that
# sends requests to:
#
# POST /api/interactions
#
# Body:
#
# {
#     "destination_id": 1,
#     "interaction_type": "view"
# }
# ============================================================

@app.route(
    "/api/interactions",
    methods=["POST"]
)
def add_interaction():

    connection = None
    cursor = None

    try:

        data = request.get_json(
            silent=True
        ) or {}

        destination_id = data.get(
            "destination_id"
        )

        interaction_type = data.get(
            "interaction_type",
            "view"
        )

        if not destination_id:

            return jsonify({

                "success": False,

                "error":
                "destination_id is required"

            }), 400

        connection = get_db_connection()

        cursor = connection.cursor()

        # Check destination.

        cursor.execute(
            """
            SELECT id
            FROM destinations
            WHERE id = %s
            """,
            (destination_id,)
        )

        destination = cursor.fetchone()

        if not destination:

            return jsonify({

                "success": False,

                "error":
                "Destination not found"

            }), 404

        # Insert interaction.

        query = """
            INSERT INTO destination_interactions
            (
                destination_id,
                interaction_type
            )
            VALUES (%s, %s)
        """

        cursor.execute(
            query,
            (
                destination_id,
                interaction_type
            )
        )

        connection.commit()

        return jsonify({

            "success": True,

            "message":
            "Interaction recorded",

            "destination_id":
            destination_id,

            "interaction_type":
            interaction_type

        }), 201

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({

            "success": False,

            "error": str(e)

        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# GET INTERACTION COUNTS
#
# Useful for testing.
#
# GET /api/interactions
#
# Returns all destinations and their interaction counts.
# ============================================================

@app.route(
    "/api/interactions",
    methods=["GET"]
)
def get_interactions():

    connection = None
    cursor = None

    try:

        connection = get_db_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        query = """
            SELECT
                d.id,
                d.name,
                COUNT(di.id) AS interaction_count

            FROM destinations d

            LEFT JOIN destination_interactions di
                ON d.id = di.destination_id

            GROUP BY
                d.id,
                d.name

            ORDER BY
                interaction_count DESC,
                d.id ASC
        """

        cursor.execute(query)

        results = cursor.fetchall()

        return jsonify({
            "interactions": results
        }), 200

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


# ============================================================
# ALL DESTINATIONS
# ============================================================

@app.route(
    "/api/destinations",
    methods=["GET"]
)
def destinations():

    try:

        data = get_all_destinations()

        return jsonify({
            "destinations": data
        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# DESTINATION DETAILS
# ============================================================

@app.route(
    "/api/destinations/<int:destination_id>",
    methods=["GET"]
)
def destination(destination_id):

    try:

        destination_data = get_destination_by_id(
            destination_id
        )

        if not destination_data:

            return jsonify({
                "message": "Destination not found"
            }), 404

        spots = get_destination_spots(
            destination_id
        )

        destination_data["spots"] = spots

        return jsonify(
            destination_data
        ), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

# ============================================================
# GET CURRENT WEATHER FOR A DESTINATION
# ============================================================

@app.route(
    "/api/destinations/<int:destination_id>/weather",
    methods=["GET"]
)
def destination_weather(destination_id):

    result, status_code = get_destination_weather(
        destination_id
    )

    return jsonify(result), status_code

# ============================================================
# EXPLORE SEARCH
# ============================================================

@app.route(
    "/api/explore/search",
    methods=["GET"]
)
def explore_search():

    search_query = (
        request.args.get("q") or ""
    ).strip()

    user_id = request.args.get(
        "user_id",
        type=int
    )

    if not search_query:

        return jsonify({
            "message": "Search query is required"
        }), 400

    try:

        destinations = search_destinations(
            search_query
        )

        # Save search history only if
        # a user is logged in.

        if user_id:

            save_search(
                user_id,
                search_query
            )

        return jsonify({

            "search_query":
            search_query,

            "destinations":
            destinations

        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# SEARCH HISTORY
# ============================================================

@app.route(
    "/api/search-history/<int:user_id>",
    methods=["GET"]
)
def search_history(user_id):

    try:

        history = get_search_history(
            user_id
        )

        return jsonify({
            "history": history
        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# SAVE PLACE
# ============================================================

@app.route(
    "/api/saved-places",
    methods=["POST"]
)
def save_destination():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get(
        "user_id"
    )

    destination_id = data.get(
        "destination_id"
    )

    if not user_id or not destination_id:

        return jsonify({

            "message":
            "user_id and destination_id are required"

        }), 400

    try:

        save_place(
            user_id,
            destination_id
        )

        return jsonify({

            "message":
            "Destination saved successfully"

        }), 201

    except mysql.connector.IntegrityError:

        return jsonify({

            "message":
            "Destination is already saved"

        }), 409

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# GET SAVED PLACES
# ============================================================

@app.route(
    "/api/saved-places/<int:user_id>",
    methods=["GET"]
)
def saved_destinations(user_id):

    try:

        destinations = get_saved_places(
            user_id
        )

        return jsonify({

            "saved_places":
            destinations

        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# REMOVE SAVED PLACE
# ============================================================

@app.route(
    "/api/saved-places",
    methods=["DELETE"]
)
def remove_destination():

    data = request.get_json(
        silent=True
    ) or {}

    user_id = data.get(
        "user_id"
    )

    destination_id = data.get(
        "destination_id"
    )

    if not user_id or not destination_id:

        return jsonify({

            "message":
            "user_id and destination_id are required"

        }), 400

    try:

        remove_saved_place(
            user_id,
            destination_id
        )

        return jsonify({

            "message":
            "Destination removed from saved places"

        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# PLAN MY TRIP
# ============================================================


@app.route("/api/plan-trip", methods=["POST"])
def plan_trip():
    try:
        data = request.get_json() or {}

        user_id = data.get("user_id")

        if not user_id:
            return jsonify({
                "success": False,
                "message": "Please log in to get personalized recommendations."
            }), 401

        # Convert budget safely
        budget_value = data.get("budget", 0)
        unlimited_budget = (
            str(budget_value).strip().lower()
            in ("unlimited", "no limit", "any")
        )

        budget = 0 if unlimited_budget else float(budget_value or 0)

        preferences = {
    "starting_city": data.get("starting_city"),
    "travel_type": data.get("travel_type", "Any"),
    "budget": budget,
    "unlimited_budget": unlimited_budget,
    "number_of_people": data.get("number_of_people", 1),
    "number_of_days": data.get("number_of_days", 3),
    "companion": data.get("companion", "Any")
}

        # Save the submitted preferences for this user
        save_trip_preferences(
            user_id,
            preferences["travel_type"],
            None if unlimited_budget else budget,
            preferences["companion"],
            preferences["number_of_people"],
            preferences["number_of_days"],
            data.get("start_date")
        )

        # Generate recommendations using the hybrid algorithm
        recommendations = get_recommendations(
            preferences,
            user_id=user_id,
            limit=6
        )

        return jsonify({
            "success": True,
            "recommendations": recommendations
        }), 200

    except Exception as e:
        print("Plan trip error:", str(e))
        return jsonify({
            "success": False,
            "message": "Unable to generate recommendations.",
            "error": str(e)
        }), 500



# ============================================================
# CREATE TRIP
# ============================================================

@app.route("/api/my-trips", methods=["POST"])
def add_trip():

    data = request.get_json(silent=True) or {}

    required_fields = [
        "user_id",
        "destination_id",
        "number_of_days",
        "start_date"
    ]

    for field in required_fields:
        if data.get(field) is None:
            return jsonify({
                "message": f"{field} is required"
            }), 400

    try:
        result = create_trip(
            data.get("user_id"),
            data.get("destination_id"),
            data.get("trip_type"),
            data.get("number_of_people", 1),
            data.get("number_of_days"),
            data.get("budget"),
            data.get("start_date"),
            data.get("end_date"),
            data.get("notes")
        )

        # Updated trip_service.py may return both values.
        if isinstance(result, tuple):
            trip_id, already_exists = result
        else:
            trip_id = result
            already_exists = False

        if already_exists:
            return jsonify({
                "message": "This trip already exists",
                "trip_id": trip_id,
                "already_exists": True
            }), 200

        return jsonify({
            "message": "Trip created successfully",
            "trip_id": trip_id,
            "already_exists": False
        }), 201

    except Exception as e:
        return jsonify({
            "message": str(e)
        }), 500



# ============================================================
# GET MY TRIPS
# ============================================================

@app.route(
    "/api/my-trips/<int:user_id>",
    methods=["GET"]
)
def my_trips(user_id):

    try:

        trips = get_user_trips(
            user_id
        )

        return jsonify({
            "trips": trips
        }), 200

    except Exception as e:

        return jsonify({
            "message": str(e)
        }), 500

# ============================================================
# UPDATE TRIP DETAILS
# ============================================================

@app.route("/api/my-trips/<int:trip_id>", methods=["PUT"])
def edit_trip(trip_id):

    from trip_service import update_trip

    data = request.get_json(silent=True) or {}

    required_fields = [
        "user_id",
        "start_date",
        "number_of_days"
    ]

    for field in required_fields:
        if data.get(field) is None:
            return jsonify({
                "message": f"{field} is required"
            }), 400

    status = data.get("status", "upcoming")

    if status not in ["upcoming", "visited"]:
        return jsonify({
            "message": "Invalid trip status"
        }), 400

    try:
        updated = update_trip(
            trip_id,
            data.get("user_id"),
            data.get("start_date"),
            data.get("end_date"),
            data.get("number_of_days"),
            data.get("budget"),
            data.get("notes"),
            status
        )

        if updated == 0:
            return jsonify({
                "message": "Trip not found or no changes made"
            }), 404

        return jsonify({
            "message": "Trip updated successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "message": str(e)
        }), 500


# ============================================================
# UPDATE TRIP STATUS
# ============================================================

@app.route(
    "/api/my-trips/<int:trip_id>/status",
    methods=["PUT"]
)
def edit_trip_status(trip_id):

    from trip_service import update_trip_status

    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")
    status = data.get("status")

    if not user_id or status not in ["upcoming", "visited"]:
        return jsonify({
            "message": "Valid user_id and status are required"
        }), 400

    try:
        updated = update_trip_status(
            trip_id,
            user_id,
            status
        )

        if updated == 0:
            return jsonify({
                "message": "Trip not found or status unchanged"
            }), 404

        return jsonify({
            "message": "Trip status updated successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "message": str(e)
        }), 500

# ============================================================
# DELETE UPCOMING TRIP
# ============================================================

@app.route("/api/my-trips/<int:trip_id>", methods=["DELETE"])
def delete_my_trip(trip_id):

    from trip_service import delete_trip

    data = request.get_json(silent=True) or {}

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "message": "user_id is required"
        }), 400

    try:
        deleted = delete_trip(
            trip_id,
            user_id
        )

        if not deleted:
            return jsonify({
                "message": "Upcoming trip not found"
            }), 404

        return jsonify({
            "message": "Trip removed successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "message": str(e)
        }), 500

@app.route("/api/routes", methods=["GET"])
def list_routes():

    routes = []

    for rule in app.url_map.iter_rules():

        routes.append({
            "endpoint": rule.endpoint,
            "methods": sorted(
                rule.methods
            ),
            "path": str(rule)
        })

    return jsonify({
        "routes": routes
    })

# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
# =============================================