
from db import get_db_connection
from math import sqrt


# ==================================================
# 1. HELPER FUNCTIONS
# ==================================================

def safe_number(value, default=0):
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def normalize(value):
    if value is None:
        return ""
    return str(value).strip().lower().replace("_", " ").replace("-", " ")


def get_preference(preferences, *keys, default=None):
    for key in keys:
        if key in preferences and preferences[key] is not None:
            return preferences[key]
    return default


def first_present(row, *keys):
    for key in keys:
        if key in row and row[key] is not None and row[key] != "":
            return row[key]
    return None


def clamp(value, minimum=0, maximum=100):
    return max(minimum, min(maximum, value))


def is_any(value):
    return normalize(value) in ("", "any", "all", "no preference")


# ==================================================
# 2. DATABASE
# ==================================================

def get_all_destination_data():
    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM destinations")
        rows = cursor.fetchall()
        cursor.close()
        return rows
    finally:
        connection.close()


# ==================================================
# 3. CONTENT-BASED SCORING
# ==================================================

def calculate_type_score(destination, preferences):
    preferred = get_preference(
        preferences, "travel_type", "travelType", default="Any"
    )

    if is_any(preferred):
        return 100

    actual = normalize(first_present(
        destination, "destination_type", "type", "category"
    ))

    preferred = normalize(preferred)

    if not actual:
        return 50
    if actual == preferred:
        return 100
    if preferred in actual or actual in preferred:
        return 80
    return 20


def calculate_budget_score(destination, preferences):
    unlimited = get_preference(
        preferences, "unlimited_budget", "unlimitedBudget", default=False
    )

    budget = safe_number(get_preference(
        preferences, "budget", default=0
    ))

    if unlimited or budget <= 0:
        return 100

    minimum = safe_number(first_present(
        destination, "budget_min", "min_budget", "minimum_budget"
    ))

    maximum = safe_number(first_present(
        destination, "budget_max", "max_budget", "maximum_budget"
    ))

    if minimum == 0 and maximum == 0:
        return 50

    if minimum <= budget <= maximum:
        return 100

    if budget < minimum:
        return clamp(100 - ((minimum - budget) / max(minimum, 1)) * 100)

    return clamp(100 - ((budget - maximum) / max(budget, 1)) * 100)


def calculate_days_score(destination, preferences):
    days = safe_number(get_preference(
        preferences, "number_of_days", "days", default=0
    ))

    recommended = safe_number(first_present(
        destination, "recommended_days", "number_of_days",
        "days", "ideal_days"
    ))

    if days <= 0 or recommended <= 0:
        return 50

    difference = abs(days - recommended)
    return clamp(100 - difference / max(days, recommended) * 100)


def calculate_destination_score(destination, preferences):
    preferred = get_preference(
        preferences, "preferred_destination", "destination",
        default="Any"
    )

    if is_any(preferred):
        return 100

    name = normalize(first_present(
        destination, "name", "destination_name"
    ))
    preferred = normalize(preferred)

    if not name:
        return 50
    if name == preferred:
        return 100
    if preferred in name or name in preferred:
        return 80
    return 20


def calculate_weather_score(destination, preferences):
    preferred = normalize(get_preference(
        preferences, "weather_preference", "weather", default="Any"
    ))

    if is_any(preferred):
        return 100

    actual = normalize(first_present(
        destination, "weather", "weather_type", "climate"
    ))

    if not actual:
        return 50

    groups = {
        "cool": ["cool", "cold", "winter", "snow"],
        "warm": ["warm", "hot", "summer", "tropical"],
        "pleasant": ["pleasant", "moderate", "mild"]
    }

    expected = groups.get(preferred, [preferred])

    if any(item in actual for item in expected):
        return 100

    return 25


def calculate_people_score(destination, preferences):
    people = safe_number(get_preference(
        preferences, "number_of_people", "people", default=1
    ), 1)

    minimum = first_present(
        destination, "min_group_size", "minimum_group_size", "min_people"
    )
    maximum = first_present(
        destination, "max_group_size", "maximum_group_size", "max_people"
    )

    # No group-size information in DB means no group-size penalty.
    if minimum is None and maximum is None:
        return 100

    if people <= 0:
        return 50

    minimum = safe_number(minimum, 1)
    maximum = safe_number(maximum, 999999)

    return 100 if minimum <= people <= maximum else 40


def calculate_companion_score(destination, preferences):
    companion = normalize(get_preference(
        preferences, "companion", "travel_company", default="Any"
    ))

    if is_any(companion):
        return 100

    actual = normalize(first_present(
        destination, "suitable_for", "travel_companion",
        "companion_type", "best_for"
    ))

    # Do not invent companion suitability without DB data.
    if not actual:
        return 100

    if companion in actual or "all" in actual or "everyone" in actual:
        return 100

    return 40


def calculate_content_score(destination, preferences):
    scores = {
        "type": calculate_type_score(destination, preferences),
        "budget": calculate_budget_score(destination, preferences),
        "days": calculate_days_score(destination, preferences),
        "destination": calculate_destination_score(destination, preferences),
        "weather": calculate_weather_score(destination, preferences),
        "people": calculate_people_score(destination, preferences),
        "companion": calculate_companion_score(destination, preferences)
    }

    total = (
        scores["type"] * 0.25
        + scores["budget"] * 0.20
        + scores["days"] * 0.15
        + scores["destination"] * 0.10
        + scores["weather"] * 0.10
        + scores["people"] * 0.10
        + scores["companion"] * 0.10
    )

    return round(clamp(total), 2)


# ==================================================
# 4. KNOWLEDGE-BASED SCORING
# ==================================================

def calculate_knowledge_score(destination, preferences):
    total = (
        calculate_type_score(destination, preferences) * 0.25
        + calculate_budget_score(destination, preferences) * 0.25
        + calculate_days_score(destination, preferences) * 0.15
        + calculate_destination_score(destination, preferences) * 0.10
        + calculate_weather_score(destination, preferences) * 0.10
        + calculate_people_score(destination, preferences) * 0.075
        + calculate_companion_score(destination, preferences) * 0.075
    )

    return round(clamp(total), 2)


# ==================================================
# 5. COLLABORATIVE FILTERING PROFILES
# ==================================================

def get_user_profiles():
    connection = get_db_connection()
    profiles = {}

    queries = [
        ("""
            SELECT user_id, destination_id, COUNT(*) AS activity
            FROM search_history
            WHERE user_id IS NOT NULL
              AND destination_id IS NOT NULL
              AND destination_id IN (SELECT id FROM destinations)
            GROUP BY user_id, destination_id
        """, 1),

        ("""
            SELECT user_id, destination_id, COUNT(*) AS activity
            FROM saved_places
            WHERE user_id IS NOT NULL
              AND destination_id IS NOT NULL
              AND destination_id IN (SELECT id FROM destinations)
            GROUP BY user_id, destination_id
        """, 2),

        ("""
            SELECT user_id, destination_id, COUNT(*) AS activity
            FROM trips
            WHERE user_id IS NOT NULL
              AND destination_id IS NOT NULL
              AND destination_id IN (SELECT id FROM destinations)
            GROUP BY user_id, destination_id
        """, 3)
    ]

    try:
        cursor = connection.cursor(dictionary=True)

        for query, weight in queries:
            try:
                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    uid = row.get("user_id")
                    did = row.get("destination_id")

                    if uid is None or did is None:
                        continue

                    try:
                        did = int(did)
                    except (ValueError, TypeError):
                        continue

                    if did <= 0:
                        continue

                    uid = str(uid)
                    profiles.setdefault(uid, {})

                    activity = safe_number(row.get("activity"), 1)

                    profiles[uid][did] = (
                        profiles[uid].get(did, 0) + activity * weight
                    )

            except Exception:
                connection.rollback()
                continue

        cursor.close()
    finally:
        connection.close()

    return profiles


def cosine_similarity(profile_a, profile_b):
    items = set(profile_a) | set(profile_b)

    if not items:
        return 0

    dot = sum(
        profile_a.get(item, 0) * profile_b.get(item, 0)
        for item in items
    )

    magnitude_a = sqrt(sum(v ** 2 for v in profile_a.values()))
    magnitude_b = sqrt(sum(v ** 2 for v in profile_b.values()))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot / (magnitude_a * magnitude_b)


def calculate_rating_popularity(destination):
    rating = safe_number(first_present(
        destination, "rating", "average_rating", "avg_rating"
    ))

    if rating <= 0:
        return 50

    if rating <= 5:
        return clamp(rating * 20)

    return clamp(rating)


def calculate_collaborative_scores(destinations, user_id):
    profiles = get_user_profiles()
    scores = {}

    current_user = str(user_id) if user_id is not None else None

    for destination in destinations:
        try:
            did = int(destination.get("id"))
        except (ValueError, TypeError):
            continue

        if did <= 0:
            continue

        fallback = calculate_rating_popularity(destination)

        if current_user is None or current_user not in profiles:
            scores[did] = fallback
            continue

        user_profile = profiles[current_user]

        if not user_profile:
            scores[did] = fallback
            continue

        if did in user_profile:
            scores[did] = fallback
            continue

        weighted_score = 0
        similarity_total = 0

        for other_user, other_profile in profiles.items():
            if other_user == current_user:
                continue

            similarity = cosine_similarity(user_profile, other_profile)

            if similarity <= 0:
                continue

            activity = other_profile.get(did, 0)

            if activity > 0:
                weighted_score += similarity * min(activity, 5)
                similarity_total += similarity

        if similarity_total == 0:
            scores[did] = fallback
        else:
            average = weighted_score / similarity_total
            scores[did] = clamp((average / 5) * 100)

    return scores


# ==================================================
# 6. MATCH EXPLANATION
# ==================================================

def create_match_explanation(destination, preferences):
    reasons = []

    preferred_type = get_preference(
        preferences, "travel_type", "travelType", default="Any"
    )

    if not is_any(preferred_type):
        if calculate_type_score(destination, preferences) >= 80:
            reasons.append("matches your preferred travel type")

    budget = safe_number(get_preference(
        preferences, "budget", default=0
    ))

    unlimited = get_preference(
        preferences, "unlimited_budget", default=False
    )

    if unlimited or budget <= 0:
        reasons.append("no budget limit was applied")
    elif calculate_budget_score(destination, preferences) >= 75:
        reasons.append("fits your budget")

    if calculate_days_score(destination, preferences) >= 70:
        reasons.append("suits your travel duration")

    weather = get_preference(
        preferences, "weather_preference", default="Any"
    )

    if not is_any(weather):
        if calculate_weather_score(destination, preferences) >= 75:
            reasons.append("matches your stored weather preference")

    if not reasons:
        return "Recommended based on the overall hybrid score."

    return "This destination " + ", ".join(reasons) + "."


# ==================================================
# 7. FORMAT RECOMMENDATION
# ==================================================

def format_recommendation(destination, match_percentage):
    destination_id = destination.get("id")
    name = first_present(destination, "name", "destination_name")

    image_url = first_present(
        destination, "image_url", "image", "photo"
    )

    if isinstance(image_url, str):
        if not image_url.strip().lower().startswith(("http://", "https://")):
            image_url = None

    destination_type = first_present(
        destination, "destination_type", "destination_type_name",
        "type", "category"
    )

    budget_min = first_present(
        destination, "budget_min", "min_budget", "minimum_budget"
    )

    budget_max = first_present(
        destination, "budget_max", "max_budget", "maximum_budget"
    )

    recommended_days = first_present(
        destination, "recommended_days", "number_of_days",
        "days", "ideal_days"
    )

    rating = first_present(
        destination, "rating", "average_rating", "avg_rating"
    )

    if budget_min is not None and budget_max is not None:
        budget_range = f"₹{budget_min} - ₹{budget_max}"
    elif budget_min is not None:
        budget_range = f"From ₹{budget_min}"
    elif budget_max is not None:
        budget_range = f"Up to ₹{budget_max}"
    else:
        budget_range = "Not available"

    return {
        "destination_id": destination_id,
        "id": destination_id,
        "name": name or "Unknown Destination",
        "image_url": image_url,
        "image": image_url,
        "destination_type": destination_type,
        "type": destination_type,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "budget_range": budget_range,
        "recommended_days": recommended_days,
        "rating": rating,
        "match_percentage": round(match_percentage, 2),
        "matchPercentage": round(match_percentage, 2)
    }


# ==================================================
# 8. MAIN HYBRID RECOMMENDER
# ==================================================

def get_recommendations(preferences, user_id=None, limit=3):
    destinations = get_all_destination_data()

    if not destinations:
        return []

    collaborative_scores = calculate_collaborative_scores(
        destinations, user_id
    )

    final_recommendations = []

    for destination in destinations:
        try:
            destination_id = int(destination.get("id"))
        except (ValueError, TypeError):
            continue

        if destination_id <= 0:
            continue

        content_score = calculate_content_score(
            destination, preferences
        )

        collaborative_score = collaborative_scores.get(
            destination_id,
            calculate_rating_popularity(destination)
        )

        knowledge_score = calculate_knowledge_score(
            destination, preferences
        )

        # Exact hybrid weights: 50% + 25% + 25%.
        hybrid_score = (
            content_score * 0.50
            + collaborative_score * 0.25
            + knowledge_score * 0.25
        )

        recommendation = format_recommendation(
            destination, hybrid_score
        )

        recommendation["content_score"] = round(content_score, 2)
        recommendation["collaborative_score"] = round(
            collaborative_score, 2
        )
        recommendation["knowledge_score"] = round(
            knowledge_score, 2
        )

        recommendation["match_explanation"] = create_match_explanation(
            destination, preferences
        )

        recommendation["explanation"] = recommendation["match_explanation"]

        recommendation["hybrid_weights"] = {
            "content_based": 50,
            "collaborative": 25,
            "knowledge_based": 25
        }

        final_recommendations.append(recommendation)

    final_recommendations.sort(
        key=lambda item: item["match_percentage"],
        reverse=True
    )

    try:
        limit = max(1, int(limit))
    except (ValueError, TypeError):
        limit = 3

    return final_recommendations[:limit]
