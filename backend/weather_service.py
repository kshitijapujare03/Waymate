
import requests
from db import get_db_connection


def get_destination_weather(destination_id):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch destination coordinates from MySQL.
        cursor.execute("""
            SELECT id, name, latitude, longitude
            FROM destinations
            WHERE id = %s
        """, (destination_id,))

        destination = cursor.fetchone()

        if not destination:
            return {
                "success": False,
                "message": "Destination not found."
            }, 404

        latitude = destination.get("latitude")
        longitude = destination.get("longitude")

        if latitude is None or longitude is None:
            return {
                "success": False,
                "message": "Weather coordinates are unavailable."
            }, 404

        # Fetch current weather using Open-Meteo.
        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "weather_code,"
                "wind_speed_10m"
            ),
            "timezone": "auto"
        }

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        weather_data = response.json()
        current = weather_data.get("current", {})

        # Convert WMO weather codes into readable descriptions.
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            71: "Slight snowfall",
            73: "Moderate snowfall",
            75: "Heavy snowfall",
            80: "Rain showers",
            81: "Moderate rain showers",
            82: "Heavy rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with hail",
            99: "Heavy thunderstorm with hail"
        }

        weather_code = current.get("weather_code")

        return {
            "success": True,
            "destination": destination["name"],
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "condition": weather_codes.get(
                weather_code,
                "Weather information unavailable"
            ),
            "weather_code": weather_code,
            "time": current.get("time"),
            "timezone": weather_data.get("timezone"),
            "temperature_unit": "°C",
            "wind_speed_unit": "km/h",
            "source": "Open-Meteo"
        }, 200

    except requests.RequestException as e:
        print("Weather API error:", str(e))

        return {
            "success": False,
            "message": "Unable to fetch current weather."
        }, 503

    except Exception as e:
        print("Destination weather error:", str(e))

        return {
            "success": False,
            "message": "Unable to retrieve destination weather."
        }, 500

    finally:
        cursor.close()
        connection.close()
