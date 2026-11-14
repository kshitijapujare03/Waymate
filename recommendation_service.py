
from db import get_db_connection
from math import sqrt


# --------------------------------------------------
# 1. FETCH ALL DESTINATIONS FROM MYSQL
# --------------------------------------------------

def get_all_destination_data():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                id, name, location, destination_type, description,
                budget_min, budget_max, weather, packing_essentials,
                rating, image_url, is_popular, recommended_days,
                popularity_value
            FROM destinations
        """)
        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


# --------------------------------------------------
# 2. HELPER FUNCTIONS
# --------------------------------------------------

def safe_number(value, default=0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize(value):
    return str(value or "").strip().lower()


def get_preference(preferences, *keys, default=None):
    for key in keys:
        if key in preferences and preferences[key] is not None:
            return preferences[key]
    return default


def calculate_rating_popularity(destination):
    """
    Missing or zero rating gets a neutral score.
    No fake rating is stored in the database.
    """

    rating = safe_number(destination.get("rating"))
    popularity = safe_number(destination.get("popularity_value"))

    if rating <= 0:
        rating_score = 50
    else:
        rating_score = min(100, (rating / 5) * 100)

    popularity_score = min(100, max(0, popularity))

    return round(
        rating_score * 0.70 + popularity_score * 0.30,
        2
    )


# --------------------------------------------------
# 3. CATEGORY NORMALIZATION FOR DIVERSITY
# --------------------------------------------------

def get_category_group(destination_type):
    category = normalize(destination_type)

    if not category:
        return "unknown"

    if any(word in category for word in ["heritage", "historical", "history", "cultural"]):
        return "heritage"

    if any(word in category for word in ["nature", "forest", "waterfall"]):
        return "nature"

    if any(word in category for word in ["mountain", "hill"]):
        return "mountain"

    if "beach" in category:
        return "beach"

    if any(word in category for word in ["religion", "religious", "spiritual"]):
        return "religion"

    if any(word in category for word in ["adventure", "trekking"]):
        return "adventure"

    if "desert" in category:
        return "desert"

    if "wildlife" in category:
        return "wildlife"

    return category


# --------------------------------------------------
# 4. CONTENT-BASED FILTERING
# --------------------------------------------------

def calculate_type_score(destination, preferences):
    preferred_type = normalize(
        get_preference(
            preferences,
            "destination_type",
            "travelType",
            default="any"
        )
    )

    actual_type = normalize(destination.get("destination_type"))

    if not preferred_type or preferred_type in (
        "any", "all", "not decided"
    ):
        return 100

    if preferred_type == actual_type:
        return 100

    if preferred_type in actual_type or actual_type in preferred_type:
        return 75

    return 20


def calculate_budget_score(destination, preferences):
    budget = safe_number(
        get_preference(preferences, "budget", default=0)
    )

    minimum = safe_number(destination.get("budget_min"))
    maximum = safe_number(destination.get("budget_max"))

    if budget <= 0:
        return 100

    if minimum <= budget <= maximum:
        return 100

    if budget >= minimum and maximum > 0:
        return 75

    if budget < minimum:
        difference = minimum - budget
        return max(
            0,
            100 - (difference / max(minimum, 1)) * 100
        )

    return 50


def calculate_days_score(destination, preferences):
    days = safe_number(
        get_preference(
            preferences,
            "number_of_days",
            "travelDays",
            default=0
        )
    )

    recommended_days = safe_number(
        destination.get("recommended_days")
    )

    if days <= 0 or recommended_days <= 0:
        return 100

    difference = abs(days - recommended_days)

    return max(
        0,
        100 - (difference / max(recommended_days, 1)) * 100
    )


def calculate_destination_score(destination, preferences):
    preferred = normalize(
        get_preference(
            preferences,
            "preferred_destination",
            "preferredDestination",
            default=""
        )
    )

    name = normalize(destination.get("name"))

    if not preferred or preferred in (
        "any", "not decided", "none"
    ):
        return 100

    if preferred == name:
        return 100

    if preferred in name or name in preferred:
        return 75

    return 30


# --------------------------------------------------
# 5. WEATHER-BASED MATCHING
# --------------------------------------------------

def calculate_weather_score(destination, preferences):
    preferred_weather = normalize(
        get_preference(
            preferences,
            "weather_preference",
            "weatherPreference",
            default="any"
        )
    )

    actual_weather = normalize(destination.get("weather"))

    if not preferred_weather or preferred_weather in (
        "any", "any weather", "all", "not decided"
    ):
        return 100

    weather_groups = {
        "sunny": ["sunny", "hot", "warm", "dry", "clear"],
        "cold": ["cold", "cool", "snow", "winter", "chilly"],
        "rainy": ["rain", "rainy", "monsoon", "wet"]
    }

    selected_words = weather_groups.get(
        preferred_weather,
        [preferred_weather]
    )

    if any(word in actual_weather for word in selected_words):
        return 100

    return 20


# --------------------------------------------------
# 6. CONTENT-BASED SCORE
# --------------------------------------------------

def calculate_content_score(destination, preferences):
    type_score = calculate_type_score(destination, preferences)
    budget_score = calculate_budget_score(destination, preferences)
    days_score = calculate_days_score(destination, preferences)
    destination_score = calculate_destination_score(
        destination, preferences
    )
    weather_score = calculate_weather_score(
        destination, preferences
    )

    score = (
        type_score * 0.30 +
        budget_score * 0.25 +
        days_score * 0.15 +
        destination_score * 0.15 +
        weather_score * 0.15
    )

    return round(score, 2)


# --------------------------------------------------
# 7. KNOWLEDGE-BASED SCORE
# --------------------------------------------------

def calculate_knowledge_score(destination, preferences):
    type_score = calculate_type_score(destination, preferences)
    budget_score = calculate_budget_score(destination, preferences)
    days_score = calculate_days_score(destination, preferences)
    destination_score = calculate_destination_score(
        destination, preferences
    )
    weather_score = calculate_weather_score(
        destination, preferences
    )

    score = (
        type_score * 0.30 +
        budget_score * 0.30 +
        days_score * 0.15 +
        destination_score * 0.15 +
        weather_score * 0.10
    )

    return round(score, 2)


# --------------------------------------------------
# 8. COLLABORATIVE FILTERING - USER PROFILES
# --------------------------------------------------

def get_user_profiles():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT user_id, destination_id, SUM(weight) AS score
            FROM (
                SELECT user_id, destination_id, 1 AS weight
                FROM search_history
                WHERE user_id IS NOT NULL
                  AND destination_id IS NOT NULL

                UNION ALL

                SELECT user_id, destination_id, 2 AS weight
                FROM saved_places
                WHERE user_id IS NOT NULL
                  AND destination_id IS NOT NULL

                UNION ALL

                SELECT user_id, destination_id, 3 AS weight
                FROM trips
                WHERE user_id IS NOT NULL
                  AND destination_id IS NOT NULL
            ) AS user_activity
            GROUP BY user_id, destination_id
        """)

        rows = cursor.fetchall()
        profiles = {}

        for row in rows:
            uid = str(row["user_id"])
            destination_id = int(row["destination_id"])
            score = safe_number(row["score"])

            if uid not in profiles:
                profiles[uid] = {}

            profiles[uid][destination_id] = score

        return profiles

    finally:
        cursor.close()
        connection.close()


# --------------------------------------------------
# 9. COSINE SIMILARITY
# --------------------------------------------------

def calculate_similarity(profile_a, profile_b):
    common_destinations = set(profile_a) & set(profile_b)

    dot_product = sum(
        profile_a[item] * profile_b[item]
        for item in common_destinations
    )

    magnitude_a = sqrt(
        sum(value ** 2 for value in profile_a.values())
    )

    magnitude_b = sqrt(
        sum(value ** 2 for value in profile_b.values())
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (magnitude_a * magnitude_b)


# --------------------------------------------------
# 10. COLLABORATIVE FILTERING SCORE
# --------------------------------------------------

def calculate_collaborative_scores(destinations, user_id=None):
    destination_ids = [
        int(destination["id"]) for destination in destinations
    ]

    scores = {}

    # Anonymous user: use rating and popularity
    if user_id is None:
        for destination in destinations:
            destination_id = int(destination["id"])

            scores[destination_id] = (
                calculate_rating_popularity(destination)
            )

        return scores

    try:
        profiles = get_user_profiles()
        current_id = str(user_id)

        target_profile = profiles.get(current_id, {})

        # User has no activity: use rating and popularity
        if not target_profile:
            for destination in destinations:
                destination_id = int(destination["id"])

                scores[destination_id] = (
                    calculate_rating_popularity(destination)
                )

            return scores

        similarities = {}

        for other_user, other_profile in profiles.items():
            if other_user == current_id:
                continue

            similarity = calculate_similarity(
                target_profile,
                other_profile
            )

            if similarity > 0:
                similarities[other_user] = similarity

        for destination_id in destination_ids:

            # Already interacted destinations get neutral score
            if destination_id in target_profile:
                scores[destination_id] = 50
                continue

            weighted_total = 0
            similarity_total = 0

            for other_user, similarity in similarities.items():
                other_profile = profiles[other_user]

                if destination_id in other_profile:
                    weighted_total += (
                        similarity * other_profile[destination_id]
                    )
                    similarity_total += similarity

            if similarity_total > 0:
                predicted = weighted_total / similarity_total

                scores[destination_id] = min(
                    100,
                    (predicted / 6) * 100
                )
            else:
                scores[destination_id] = (
                    calculate_rating_popularity(
                        next(
                            d for d in destinations
                            if int(d["id"]) == destination_id
                        )
                    )
                )

        return {
            key: round(value, 2)
            for key, value in scores.items()
        }

    except Exception:
        # Safe fallback if collaborative data is unavailable
        for destination in destinations:
            destination_id = int(destination["id"])

            scores[destination_id] = (
                calculate_rating_popularity(destination)
            )

        return scores


# --------------------------------------------------
# 11. EXPLANATION FOR FRONTEND
# --------------------------------------------------

def create_match_explanation(destination, preferences):
    reasons = []

    if calculate_type_score(destination, preferences) >= 75:
        reasons.append("matches your preferred travel type")

    if calculate_budget_score(destination, preferences) >= 75:
        reasons.append("fits your budget")

    if calculate_days_score(destination, preferences) >= 70:
        reasons.append("suits your travel duration")

    if calculate_weather_score(destination, preferences) >= 75:
        reasons.append("matches your weather preference")

    if not reasons:
        return "Recommended based on overall destination suitability."

    return "This destination " + ", ".join(reasons) + "."


# --------------------------------------------------
# 12. CATEGORY-DIVERSE RECOMMENDATIONS
# --------------------------------------------------

def select_diverse_recommendations(recommendations, limit):
    selected = []
    used_categories = set()

    # First pass: choose different destination categories
    for destination in recommendations:
        category = get_category_group(
            destination.get("destination_type")
        )

        if category not in used_categories:
            selected.append(destination)
            used_categories.add(category)

        if len(selected) >= limit:
            return selected

    # Second pass: fill remaining places if needed
    selected_ids = {
        destination["id"] for destination in selected
    }

    for destination in recommendations:
        if destination["id"] not in selected_ids:
            selected.append(destination)
            selected_ids.add(destination["id"])

        if len(selected) >= limit:
            break

    return selected


# --------------------------------------------------
# 13. MAIN HYBRID RECOMMENDATION FUNCTION
# --------------------------------------------------

def get_recommendations(preferences, user_id=None, limit=3):
    destinations = get_all_destination_data()

    if not destinations:
        return []

    collaborative_scores = calculate_collaborative_scores(
        destinations,
        user_id
    )

    recommendations = []

    for destination in destinations:
        destination_id = int(destination["id"])

        content_score = calculate_content_score(
            destination,
            preferences
        )

        knowledge_score = calculate_knowledge_score(
            destination,
            preferences
        )

        collaborative_score = collaborative_scores.get(
            destination_id,
            50
        )

        # Hybrid weights:
        # Content Based = 50%
        # Collaborative Filtering = 25%
        # Knowledge Based = 25%

        hybrid_score = (
            content_score * 0.50 +
            collaborative_score * 0.25 +
            knowledge_score * 0.25
        )

        destination["content_score"] = round(
            content_score, 2
        )

        destination["collaborative_score"] = round(
            collaborative_score, 2
        )

        destination["knowledge_score"] = round(
            knowledge_score, 2
        )

        destination["match_percentage"] = round(
            hybrid_score, 2
        )

        destination["match_explanation"] = (
            create_match_explanation(
                destination,
                preferences
            )
        )

        recommendations.append(destination)

    # Sort by weather match first when a weather preference is selected
    preferred_weather = normalize(
        get_preference(
            preferences,
            "weather_preference",
            "weatherPreference",
            default="any"
        )
    )

    if preferred_weather and preferred_weather not in (
        "any", "any weather", "all", "not decided"
    ):
        recommendations.sort(
            key=lambda item: (
                calculate_weather_score(item, preferences),
                item["match_percentage"]
            ),
            reverse=True
        )

    else:
        recommendations.sort(
            key=lambda item: item["match_percentage"],
            reverse=True
        )

    # Select different categories while preserving ranking order
    final_limit = max(1, int(limit))

    return select_diverse_recommendations(
        recommendations,
        final_limit
    )
