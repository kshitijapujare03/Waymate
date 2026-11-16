
from flask import Flask, request, jsonify
from flask_cors import CORS
from recommendation_service import get_recommendations
from decimal import Decimal
from datetime import date, datetime

import requests
import os
from dotenv import load_dotenv


# LOAD ENVIRONMENT VARIABLES
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path, override=True)

app = Flask(__name__)
CORS(app)


# CONVERT DATABASE VALUES INTO JSON-FRIENDLY VALUES
def clean_value(value):

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (date, datetime)):
        return value.isoformat()

    return value


# WEATHER API FUNCTION
def get_weather(city):

    api_key = os.getenv("OPENWEATHER_API_KEY")

    if not api_key:
        return {"error": "Weather API key not found"}

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }

    response = requests.get(url, params=params, timeout=10)

    if response.status_code != 200:
        return {"error": "Unable to fetch weather information"}

    data = response.json()

    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"],
        "humidity": data["main"]["humidity"]
    }


# WEATHER API ROUTE
@app.route("/api/weather", methods=["GET"])
def weather():

    city = request.args.get("city", "").strip()

    if not city:
        return jsonify({
            "error": "Please provide a city"
        }), 400

    try:
        weather_data = get_weather(city)

        if "error" in weather_data:
            return jsonify(weather_data), 502

        return jsonify(weather_data), 200

    except requests.exceptions.RequestException:
        return jsonify({
            "error": "Weather service is currently unavailable"
        }), 502


# HOME ROUTE
@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "message": "WayMate Backend is Running!",
        "port": 5001
    })


# HYBRID TRAVEL RECOMMENDATION API
@app.route("/api/plan-trip", methods=["POST"])
def plan_trip():

    data = request.get_json(silent=True) or {}

    try:

        starting_city = data.get("startingCity", "")

        travel_days = int(
            data.get("travelDays")
            or data.get("number_of_days")
            or data.get("days")
            or 0
        )

        budget = float(data.get("budget") or 0)

        travel_type = (
            data.get("travelType")
            or data.get("destination_type")
            or data.get("type")
            or "Any"
        )

        travellers = data.get("travellers", "")
        companion = data.get("travelCompany", "")

        preferred_destination = data.get(
            "preferredDestination",
            "not decided"
        )

        weather_preference = data.get(
            "weatherPreference",
            "any"
        )

        # INPUT VALIDATION
        if budget <= 0 or travel_days <= 0:
            return jsonify({
                "error": "Please provide valid budget and travel days"
            }), 400

        preferences = {
            "destination_type": travel_type,
            "budget": budget,
            "number_of_days": travel_days,
            "starting_city": starting_city,
            "number_of_people": travellers,
            "companion": companion,
            "preferred_destination": preferred_destination,
            "weather_preference": weather_preference
        }

        # USER ID
        user_id = data.get("user_id")

        if user_id not in (None, ""):
            user_id = int(user_id)
        else:
            user_id = None

        # GENERATE HYBRID RECOMMENDATIONS
        recommendations = get_recommendations(
            preferences,
            user_id,
            limit=3
        )

        # FORMAT RECOMMENDATIONS
        formatted_recommendations = []

        for destination in recommendations:

            item = dict(destination)

            item["image"] = item.get("image_url") or ""

            # Preserve NULL budget instead of showing ₹0
            item["budget"] = clean_value(
                item.get("budget_min")
            )

            item["days"] = item.get("recommended_days") or 1
            item["type"] = item.get("destination_type") or ""

            item["matchPercentage"] = clean_value(
                item.get("match_percentage", 0)
            )

            item["matchExplanation"] = item.get(
                "match_explanation", ""
            )

            # Clean database values
            for key, value in item.items():
                item[key] = clean_value(value)

            formatted_recommendations.append(item)

        return jsonify({
            "message": "Recommendations generated successfully",
            "recommendations": formatted_recommendations
        }), 200

    except Exception as e:

        app.logger.exception("Recommendation API error")

        return jsonify({
            "error": "Unable to generate recommendations",
            "details": str(e)
        }), 500


# RUN BACKEND ON PORT 5001
if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
