
import argparse
from db import get_db_connection


# These are indicative per-person budgets in INR for approximately
# 3 days / 2 nights. Travel to the destination is excluded.
DESTINATIONS = {
    40: {
        "name": "Varanasi",
        "location": "Uttar Pradesh, India",
        "type": "Heritage",
        "description": "Varanasi is one of India's oldest living cities, known for its sacred ghats along the River Ganga, ancient temples and vibrant cultural traditions.",
        "budget": (5000, 15000),
        "weather": "Hot summers, monsoon rains and cool winters",
        "packing": "Comfortable cotton clothes, walking shoes, sunscreen, reusable water bottle, modest temple-appropriate clothing and light winter wear in winter.",
        "days": 3,
        "spots": [
            ("Dashashwamedh Ghat", "A famous Ganga ghat known for its evening Ganga Aarti."),
            ("Kashi Vishwanath Temple", "One of the most important Shiva temples in India."),
            ("Assi Ghat", "A popular riverside ghat and cultural gathering place."),
            ("Sarnath", "An important Buddhist pilgrimage site near Varanasi.")
        ]
    },
    43: {
        "name": "Udaipur",
        "location": "Rajasthan, India",
        "type": "Heritage",
        "description": "Udaipur is known for its lakes, historic palaces, traditional architecture and scenic views of the Aravalli hills.",
        "budget": (7000, 20000),
        "weather": "Hot summers, monsoon rains and pleasant winters",
        "packing": "Comfortable clothes, walking shoes, sunglasses, sunscreen, water bottle and light winter clothing.",
        "days": 3,
        "spots": [
            ("City Palace", "A historic palace complex overlooking Lake Pichola."),
            ("Lake Pichola", "A scenic lake known for boat rides and waterfront views."),
            ("Jagdish Temple", "A historic Hindu temple in the old city."),
            ("Saheliyon Ki Bari", "A historic garden with fountains and landscaped pathways.")
        ]
    },
    44: {
        "name": "Jaisalmer",
        "location": "Rajasthan, India",
        "type": "Desert",
        "description": "Jaisalmer is a desert city famous for its golden sandstone architecture, historic fort, havelis and Thar Desert experiences.",
        "budget": (7000, 20000),
        "weather": "Very hot summers and pleasant winters",
        "packing": "Light cotton clothes, sunglasses, sunscreen, hat, comfortable shoes, water bottle and warm layers for cold desert nights.",
        "days": 3,
        "spots": [
            ("Jaisalmer Fort", "A historic living fort built from golden sandstone."),
            ("Sam Sand Dunes", "A popular area for experiencing the Thar Desert."),
            ("Patwon Ki Haveli", "A group of elaborately decorated historic havelis."),
            ("Gadisar Lake", "A historic lake surrounded by temples and shrines.")
        ]
    },
    57: {
        "name": "Jodhpur",
        "location": "Rajasthan, India",
        "type": "Heritage",
        "description": "Jodhpur, known as the Blue City, is famous for its historic forts, blue-painted old-town houses and traditional Rajasthani culture.",
        "budget": (6000, 18000),
        "weather": "Hot summers, limited monsoon rains and mild winters",
        "packing": "Cotton clothes, comfortable walking shoes, sunscreen, sunglasses, hat and water bottle.",
        "days": 3,
        "spots": [
            ("Mehrangarh Fort", "A hilltop fort overlooking the historic city."),
            ("Umaid Bhawan Palace", "A grand palace with a museum and heritage sections."),
            ("Jaswant Thada", "A white marble memorial near Mehrangarh Fort."),
            ("Clock Tower and Sardar Market", "A lively traditional market area.")
        ]
    },
    63: {
        "name": "Darjeeling",
        "location": "West Bengal, India",
        "type": "Hill Station",
        "description": "Darjeeling is a Himalayan hill station known for tea gardens, mountain scenery, colonial-era heritage and the Darjeeling Himalayan Railway.",
        "budget": (8000, 22000),
        "weather": "Mild summers, cold winters and frequent monsoon rain",
        "packing": "Warm layers, raincoat, comfortable walking shoes, umbrella, sunscreen and personal medicines.",
        "days": 3,
        "spots": [
            ("Tiger Hill", "A popular viewpoint for sunrise over the Himalayan ranges."),
            ("Batasia Loop", "A scenic railway loop with mountain views."),
            ("Darjeeling Himalayan Railway", "A historic narrow-gauge mountain railway."),
            ("Padmaja Naidu Himalayan Zoological Park", "A conservation-focused high-altitude zoo.")
        ]
    },
    65: {
        "name": "Shimla",
        "location": "Himachal Pradesh, India",
        "type": "Hill Station",
        "description": "Shimla is a popular Himalayan hill station known for its colonial architecture, mountain views, historic railway and lively Mall Road.",
        "budget": (8000, 22000),
        "weather": "Pleasant summers, cold winters and monsoon rains",
        "packing": "Comfortable walking shoes, warm clothes, raincoat, sunscreen, water bottle and winter accessories in colder months.",
        "days": 3,
        "spots": [
            ("The Ridge", "An open public space offering views of the surrounding hills."),
            ("Mall Road", "A popular pedestrian shopping and dining area."),
            ("Jakhoo Temple", "A hilltop temple dedicated to Lord Hanuman."),
            ("Christ Church", "A historic church overlooking the Ridge.")
        ]
    },
    84: {
        "name": "Nainital",
        "location": "Uttarakhand, India",
        "type": "Hill Station",
        "description": "Nainital is a Himalayan lake town known for Naini Lake, surrounding hills, viewpoints and pleasant mountain scenery.",
        "budget": (7000, 18000),
        "weather": "Mild summers, cold winters and monsoon rains",
        "packing": "Comfortable shoes, warm layers, raincoat, sunscreen, water bottle and personal medicines.",
        "days": 3,
        "spots": [
            ("Naini Lake", "The central lake known for boating and waterfront views."),
            ("Naina Devi Temple", "A well-known temple beside Naini Lake."),
            ("Snow View Point", "A popular viewpoint overlooking Himalayan peaks."),
            ("Tiffin Top", "A hilltop viewpoint reached by a walking trail.")
        ]
    },
    86: {
        "name": "Mysuru",
        "location": "Karnataka, India",
        "type": "Heritage",
        "description": "Mysuru is known for its royal heritage, Mysore Palace, traditional markets, gardens and cultural festivals.",
        "budget": (6000, 16000),
        "weather": "Warm summers, monsoon rains and pleasant winters",
        "packing": "Light clothes, comfortable shoes, sunscreen, umbrella during monsoon and a reusable water bottle.",
        "days": 3,
        "spots": [
            ("Mysore Palace", "A grand royal palace and major city landmark."),
            ("Chamundi Hill", "A hill with a famous temple and city views."),
            ("Brindavan Gardens", "A landscaped garden known for its musical fountain."),
            ("St. Philomena's Church", "A prominent neo-Gothic church.")
        ]
    },
    87: {
        "name": "Coorg",
        "location": "Karnataka, India",
        "type": "Nature",
        "description": "Coorg, also known as Kodagu, is a hill region famous for coffee plantations, green landscapes, waterfalls and forest scenery.",
        "budget": (8000, 22000),
        "weather": "Pleasant summers, heavy monsoon rains and cool winters",
        "packing": "Comfortable shoes, light jackets, raincoat, insect repellent, water bottle and personal medicines.",
        "days": 3,
        "spots": [
            ("Abbey Falls", "A waterfall surrounded by coffee and spice plantations."),
            ("Raja's Seat", "A garden viewpoint overlooking the surrounding hills."),
            ("Dubare Elephant Camp", "A nature and wildlife experience near the Cauvery River."),
            ("Talakaveri", "A pilgrimage site traditionally associated with the origin of the Cauvery River.")
        ]
    },
    88: {
        "name": "Ooty",
        "location": "Tamil Nadu, India",
        "type": "Hill Station",
        "description": "Ooty is a Nilgiri hill station known for its tea gardens, botanical gardens, lakes and scenic mountain railway.",
        "budget": (7000, 18000),
        "weather": "Mild summers, cool winters and monsoon rains",
        "packing": "Warm layers, comfortable walking shoes, raincoat, sunscreen and water bottle.",
        "days": 3,
        "spots": [
            ("Government Botanical Garden", "A landscaped garden with a wide variety of plants."),
            ("Ooty Lake", "A popular lake for boating and recreation."),
            ("Doddabetta Peak", "A well-known viewpoint in the Nilgiri Hills."),
            ("Nilgiri Mountain Railway", "A historic mountain railway connecting Ooty with nearby towns.")
        ]
    },
    89: {
        "name": "Munnar",
        "location": "Kerala, India",
        "type": "Nature",
        "description": "Munnar is a hill destination in Kerala known for tea plantations, mist-covered hills, waterfalls and rich biodiversity.",
        "budget": (8000, 22000),
        "weather": "Mild summers, cool winters and monsoon rains",
        "packing": "Comfortable shoes, light warm clothing, raincoat, insect repellent, sunscreen and water bottle.",
        "days": 3,
        "spots": [
            ("Eravikulam National Park", "A protected area known for the Nilgiri tahr and mountain grasslands."),
            ("Mattupetty Dam", "A scenic reservoir surrounded by hills."),
            ("Tea Museum", "A museum explaining the history of tea production in the region."),
            ("Top Station", "A popular viewpoint overlooking the Western Ghats.")
        ]
    },
    90: {
        "name": "Kaziranga National Park",
        "location": "Assam, India",
        "type": "Wildlife",
        "description": "Kaziranga National Park is a UNESCO World Heritage Site famous for its population of the Indian one-horned rhinoceros and rich wildlife habitats.",
        "budget": (8000, 22000),
        "weather": "Warm summers, heavy monsoon rains and mild winters",
        "packing": "Neutral comfortable clothing, walking shoes, hat, sunscreen, insect repellent, binoculars and personal medicines. Follow park rules.",
        "days": 3,
        "spots": [
            ("Kohora Range", "A popular visitor area for authorised wildlife safaris."),
            ("Bagori Range", "A well-known safari range in the western part of the park."),
            ("Agaratoli Range", "A visitor safari area known for its wetland habitats."),
            ("Kaziranga Orchid and Biodiversity Park", "A cultural and biodiversity attraction near the park.")
        ]
    },
    91: {
        "name": "Puri",
        "location": "Odisha, India",
        "type": "Beach",
        "description": "Puri is a coastal city known for Jagannath Temple, its long beach, religious traditions and nearby heritage attractions.",
        "budget": (6000, 16000),
        "weather": "Hot and humid summers, monsoon rains and mild winters",
        "packing": "Light cotton clothes, sandals, sunscreen, hat, water bottle and modest clothing for temple visits.",
        "days": 3,
        "spots": [
            ("Jagannath Temple", "A major Hindu pilgrimage temple. Entry restrictions apply."),
            ("Puri Beach", "A popular beach along the Bay of Bengal."),
            ("Gundicha Temple", "An important temple associated with the Jagannath tradition."),
            ("Chilika Lake", "A large brackish-water lagoon accessible on a regional day trip.")
        ]
    },
    93: {
        "name": "Konark",
        "location": "Odisha, India",
        "type": "Heritage",
        "description": "Konark is famous for its Sun Temple, a UNESCO World Heritage Site recognised for its monumental stone architecture and intricate carvings.",
        "budget": (5000, 14000),
        "weather": "Hot summers, monsoon rains and mild winters",
        "packing": "Light cotton clothes, comfortable shoes, sunscreen, hat, water bottle and modest clothing for religious sites.",
        "days": 2,
        "spots": [
            ("Konark Sun Temple", "A UNESCO World Heritage Site designed as a monumental stone chariot."),
            ("Chandrabhaga Beach", "A scenic beach near the Sun Temple."),
            ("Archaeological Museum, Konark", "A museum displaying sculptures and archaeological remains."),
            ("Ramachandi Temple", "A temple located near the Kushabhadra River mouth.")
        ]
    },
    95: {
        "name": "Khajuraho",
        "location": "Madhya Pradesh, India",
        "type": "Heritage",
        "description": "Khajuraho is internationally known for its UNESCO-listed group of medieval temples and their detailed stone sculptures and architecture.",
        "budget": (6000, 16000),
        "weather": "Hot summers, monsoon rains and cooler winters",
        "packing": "Comfortable walking shoes, light clothes, sunscreen, hat, water bottle and light winter wear when needed.",
        "days": 2,
        "spots": [
            ("Kandariya Mahadeva Temple", "One of the largest and most ornate temples in the Western Group."),
            ("Lakshmana Temple", "A major temple known for its detailed carvings."),
            ("Vishvanatha Temple", "A historic temple in the Western Group."),
            ("Eastern Group of Temples", "A group of temples with Hindu and Jain heritage.")
        ]
    }
}


TARGET_IDS = list(DESTINATIONS.keys())
BACKUP_DESTINATIONS = "destinations_backup_20261106"
BACKUP_SPOTS = "destination_spots_backup_20261106"


def table_exists(cursor, table_name):
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = %s
        """,
        (table_name,)
    )
    return cursor.fetchone()[0] > 0


def make_backups(cursor):
    for table in (BACKUP_DESTINATIONS, BACKUP_SPOTS):
        if table_exists(cursor, table):
            raise RuntimeError(
                f"Backup table {table} already exists. "
                "Stop and choose a new backup name."
            )

    cursor.execute(
        f"CREATE TABLE {BACKUP_DESTINATIONS} LIKE destinations"
    )
    cursor.execute(
        f"INSERT INTO {BACKUP_DESTINATIONS} SELECT * FROM destinations"
    )

    cursor.execute(
        f"CREATE TABLE {BACKUP_SPOTS} LIKE destination_spots"
    )
    cursor.execute(
        f"INSERT INTO {BACKUP_SPOTS} SELECT * FROM destination_spots"
    )


def preview(cursor):
    cursor.execute(
        f"""
        SELECT id, name, location, destination_type
        FROM destinations
        WHERE id IN ({",".join(["%s"] * len(TARGET_IDS))})
        ORDER BY id
        """,
        tuple(TARGET_IDS)
    )

    rows = cursor.fetchall()
    existing = {row[0]: row for row in rows}

    if len(existing) != len(TARGET_IDS):
        raise RuntimeError("One or more target destination IDs are missing.")

    print("\nPREVIEW — NO DESTINATION DATA WILL BE CHANGED\n")

    for destination_id in TARGET_IDS:
        old = existing[destination_id]
        new = DESTINATIONS[destination_id]
        print(
            f"ID {destination_id}: {old[1]} -> {new['name']} "
            f"({new['location']})"
        )

    cursor.execute("SELECT COUNT(*) FROM destinations")
    print("\nCurrent destination count:", cursor.fetchone()[0])
    print("Planned replacement count:", len(TARGET_IDS))
    print("Kabru (ID 83) is not included.")


def apply_changes(connection, cursor):
    cursor.execute("SELECT COUNT(*) FROM destinations")
    original_count = cursor.fetchone()[0]

    if original_count != 80:
        raise RuntimeError(
            f"Expected 80 destinations, found {original_count}. "
            "No changes applied."
        )

    # Verify that the selected IDs have no user-history references.
    for table in (
        "trips",
        "saved_places",
        "destination_interactions",
        "search_history"
    ):
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {table}
            WHERE destination_id IN (
                {",".join(["%s"] * len(TARGET_IDS))}
            )
            """,
            tuple(TARGET_IDS)
        )
        count = cursor.fetchone()[0]

        if count:
            raise RuntimeError(
                f"{table} contains {count} references to replacement IDs. "
                "No changes applied."
            )

    # Create complete snapshots before modifying destination data.
    make_backups(cursor)
    connection.commit()

    try:
        for destination_id, data in DESTINATIONS.items():
            cursor.execute(
                """
                UPDATE destinations
                SET
                    name = %s,
                    location = %s,
                    destination_type = %s,
                    description = %s,
                    budget_min = %s,
                    budget_max = %s,
                    weather = %s,
                    packing_essentials = %s,
                    rating = 0.00,
                    image_url = NULL,
                    is_popular = 0,
                    recommended_days = %s,
                    latitude = NULL,
                    longitude = NULL,
                    wikidata_id = NULL,
                    description_source_url = NULL,
                    popularity_value = NULL,
                    popularity_metric = NULL,
                    popularity_source = NULL,
                    popularity_year = NULL,
                    image_credit = NULL,
                    image_license = NULL,
                    image_source_url = NULL
                WHERE id = %s
                """,
                (
                    data["name"],
                    data["location"],
                    data["type"],
                    data["description"],
                    data["budget"][0],
                    data["budget"][1],
                    data["weather"],
                    data["packing"],
                    data["days"],
                    destination_id
                )
            )

            if cursor.rowcount == 0:
                raise RuntimeError(
                    f"Destination ID {destination_id} was not updated."
                )

            # Remove only the old attractions belonging to this destination.
            cursor.execute(
                "DELETE FROM destination_spots WHERE destination_id = %s",
                (destination_id,)
            )

            for spot_name, description in data["spots"]:
                cursor.execute(
                    """
                    INSERT INTO destination_spots
                    (destination_id, spot_name, description)
                    VALUES (%s, %s, %s)
                    """,
                    (destination_id, spot_name, description)
                )

        cursor.execute("SELECT COUNT(*) FROM destinations")
        final_count = cursor.fetchone()[0]

        if final_count != original_count:
            raise RuntimeError(
                "Destination count changed unexpectedly."
            )

        connection.commit()

        print("\nSUCCESS!")
        print("15 destinations updated.")
        print("Destination count remains:", final_count)
        print("Kabru (ID 83) was not changed.")
        print("Backup tables created:")
        print(" -", BACKUP_DESTINATIONS)
        print(" -", BACKUP_SPOTS)

    except Exception:
        connection.rollback()
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Safely replace selected WAYMATE destinations."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the replacements. Without this option, preview only."
    )
    args = parser.parse_args()

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        if args.apply:
            print("Applying destination replacements...")
            apply_changes(connection, cursor)
        else:
            preview(cursor)
            print("\nPreview only. No database changes were made.")
            print("Run with --apply only after reviewing the preview.")

    except Exception as error:
        connection.rollback()
        print("\nERROR:", error)

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
