
from recommendation_service import (
    calculate_content_score,
    calculate_knowledge_score,
    calculate_collaborative_scores
)

# Sample travel preferences
preferences = {
    "destination_type": "Beach",
    "budget": 10000,
    "number_of_days": 5
}

# Sample destinations (not from MySQL)
destinations = [
    {
        "id": 1,
        "destination_type": "Beach",
        "budget_min": 5000,
        "budget_max": 12000,
        "recommended_days": 5,
        "rating": 4.5
    },
    {
        "id": 2,
        "destination_type": "Hill Station",
        "budget_min": 7000,
        "budget_max": 15000,
        "recommended_days": 6,
        "rating": 4.7
    }
]

# Sample user interactions
interactions = [
    {"user_id": 1, "destination_id": 1, "weight": 1},
    {"user_id": 1, "destination_id": 2, "weight": 2},
    {"user_id": 2, "destination_id": 1, "weight": 2},
    {"user_id": 2, "destination_id": 2, "weight": 1},
    {"user_id": 3, "destination_id": 1, "weight": 3}
]

print("===== WAYMATE RECOMMENDATION TEST =====")

for destination in destinations:
    content = calculate_content_score(destination, preferences)
    knowledge = calculate_knowledge_score(destination, preferences)

    print("\nDestination ID:", destination["id"])
    print("Content-Based Score:", content)
    print("Knowledge-Based Score:", knowledge)

collaborative = calculate_collaborative_scores(
    1,
    interactions,
    destinations
)

print("\nCollaborative Filtering Scores:")
print(collaborative)

print("\n===== TEST COMPLETED =====")
