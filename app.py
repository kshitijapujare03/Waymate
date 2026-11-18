
from flask import Flask, request, jsonify
from flask_cors import CORS
from recommendation_service import get_recommendations

from decimal import Decimal
from datetime import date, datetime

from dotenv import load_dotenv
import requests
import os


# ==================================================
# 1. FLASK SETUP
# ==================================================

app = Flask(__name__)
CORS(app)

# Load .env from backend folder
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")


# ==================================================
# 2. JSON CONVERSION HELPER
# ==================================================

def clean_data(value):

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: clean_data(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [
            clean_data(item)
            for item in value
        ]

    return value


# ==================================================
# 3. HOME ROUTE
# ==================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "status": "success",
        "message": "WayMate Hybrid Recommendation API is Running!",
        "port": 5001
    })


# ==================================================
# 4. WEATHER API
# ==================================================

@app.route("/api/weather", methods=["GET"])
def get_weather():

    city = request.args.get("city")

    if not city:
        return jsonify({
            "status": "error",
            "message": "Please provide a city."
        }), 400

    if not OPENWEATHER_API_KEY:
        return jsonify({
            "status": "error",
            "message": "OpenWeather API key is missing in .env"
        }), 500

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if response.status_code != 200:
            return jsonify({
                "status": "error",
                "message": data.get(
                    "message",
                    "Unable to fetch weather"
                )
            }), response.status_code

        return jsonify({
            "status": "success",
            "city": data.get("name"),
            "temperature": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "weather": data["weather"][0]["main"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"]
        })

    except requests.RequestException as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 500


# ==================================================
# 5. HYBRID RECOMMENDATION API
# ==================================================

@app.route("/api/plan-trip", methods=["POST"])
def plan_trip():

    try:

        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "status": "error",
                "message": "Please send valid JSON data."
            }), 400

        # ------------------------------------------
        # GET USER INPUT
        # ------------------------------------------

        starting_city = data.get(
            "startingCity",
            data.get("starting_city", "")
        )

        days = data.get(
            "days",
            data.get("number_of_days")
        )

        budget = data.get("budget")

        unlimited_budget = data.get(
            "unlimitedBudget",
            data.get("unlimited_budget", False)
        )

        people = data.get(
            "number_of_people",
            data.get(
                "numberOfPeople",
                data.get("travellers", data.get("people", 1))
            )
        )

        companion = data.get(
            "companion",
            data.get(
                "travelCompany",
                data.get("travel_company", "Any")
            )
        )

        travel_type = data.get(
            "travelType",
            data.get("travel_type", "Any")
        )

        preferred_destination = data.get(
            "preferredDestination",
            data.get("preferred_destination", "Any")
        )

        weather_preference = data.get(
            "weatherPreference",
            data.get("weather_preference", "Any")
        )

        user_id = data.get("user_id")

        # ------------------------------------------
        # VALIDATE DAYS
        # ------------------------------------------

        try:
            days = int(days)

            if days <= 0:
                raise ValueError

        except (ValueError, TypeError):

            return jsonify({
                "status": "error",
                "message": "Please enter valid number of days."
            }), 400

        # ------------------------------------------
        # VALIDATE NUMBER OF PEOPLE
        # ------------------------------------------

        try:
            people = int(people)

            if people <= 0:
                raise ValueError

        except (ValueError, TypeError):

            return jsonify({
                "status": "error",
                "message": "Number of people must be greater than zero."
            }), 400

        # ------------------------------------------
        # VALIDATE BUDGET
        # ------------------------------------------

        if isinstance(unlimited_budget, str):
            unlimited_budget = (
                unlimited_budget.strip().lower()
                in ("true", "1", "yes")
            )

        if isinstance(budget, str):
            budget_text = budget.strip().lower()

            if budget_text in ("", "unlimited", "none", "null"):
                unlimited_budget = True

        if unlimited_budget:
            budget = 0

        else:

            try:
                budget = float(budget)

                if budget < 0:
                    raise ValueError

            except (ValueError, TypeError):

                return jsonify({
                    "status": "error",
                    "message": "Please enter a valid budget or select unlimited budget."
                }), 400

        # ------------------------------------------
        # VALIDATE USER ID
        # ------------------------------------------

        if user_id not in (None, ""):

            try:
                user_id = int(user_id)

                if user_id <= 0:
                    raise ValueError

            except (ValueError, TypeError):

                return jsonify({
                    "status": "error",
                    "message": "Invalid user ID."
                }), 400

        else:
            user_id = None

        # ------------------------------------------
        # PREPARE PREFERENCES
        # ------------------------------------------

        preferences = {

            "starting_city": starting_city,

            "number_of_days": days,

            "budget": budget,

            "unlimited_budget": unlimited_budget,

            "number_of_people": people,

            "companion": companion,

            "travel_type": travel_type,

            "preferred_destination": preferred_destination,

            "weather_preference": weather_preference
        }

        # ------------------------------------------
        # GET HYBRID RECOMMENDATIONS
        # ------------------------------------------

        recommendations = get_recommendations(
            preferences,
            user_id=user_id,
            limit=3
        )

        recommendations = clean_data(recommendations)

        # ------------------------------------------
        # RESPONSE NOTES
        # ------------------------------------------

        notes = [
            "Starting city is currently not used in recommendation scoring because verified distance or route data is not available.",
            "Weather preference is compared with destination weather information stored in the database. Live weather is available separately through /api/weather.",
            "Unlimited budget does not apply a budget penalty."
        ]

        if user_id is None:
            notes.append(
                "No logged-in user ID was provided. Collaborative filtering uses the popularity fallback where personal history is unavailable."
            )

        elif recommendations:
            notes.append(
                "Collaborative filtering uses available user interaction history when valid records exist."
            )

        # ------------------------------------------
        # FINAL RESPONSE
        # ------------------------------------------

        return jsonify({

            "status": "success",

            "message": "Hybrid recommendations generated successfully.",

            "preferences": clean_data(preferences),

            "recommendations": recommendations,

            "notes": notes,

            "hybrid_weights": {
                "content_based": 50,
                "collaborative": 25,
                "knowledge_based": 25
            }

        })

    except Exception as error:

        app.logger.exception("Recommendation API error")

        return jsonify({
            "status": "error",
            "message": "Unable to generate recommendations.",
            "details": str(error)
        }), 500


# ==================================================
# 6. RUN SERVER
# ==================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
