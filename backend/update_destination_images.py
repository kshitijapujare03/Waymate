
import argparse
import re
import socket
import time
import requests
import traceback
import urllib3.util.connection as urllib3_connection

from db import get_db_connection

# Wikimedia connection workaround for your Windows system.
urllib3_connection.allowed_gai_family = lambda: socket.AF_INET

API_URL = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "WaymateTravelProject/1.0 "
        "(educational project; Wikimedia Commons image verification)"
    )
}

DESTINATIONS = [
    (40, "Varanasi", "Kashi Vishwanath Temple in Varanasi.jpg"),
    (43, "Udaipur", "20191207 Lake Pichola, City Palace, Udaipur, 1516 7254.jpg"),
    (44, "Jaisalmer", "Jaisalmer, India, Jaisalmer Fort 2.jpg"),
    (57, "Jodhpur", "BluecityviewfromMehrangarhFort.jpg"),
    (63, "Darjeeling", "Kangchenjunga view from Darjeeling.jpg"),
    (65, "Shimla", "Cityscape of Shimla.jpg"),
    (84, "Nainital", "Boats on Nainital Lake.jpg"),
    (86, "Mysuru", "MYsuru palace by Gaur's.jpg"),
    (87, "Coorg", "Coorg view.jpg"),
    (88, "Ooty", "Fields Hazy Mountains Marlimund Ooty Nilgiris Aug25 A7CR 07258.jpg"),
    (89, "Munnar", "Munnar - Top Station Highway-WUS07295.jpg"),
    (
        90,
        "Kaziranga National Park",
        "An Indian rhinoceros (Rhinoceros unicornis), also known as the greater one-horned rhinoceros, at Kaziranga National Park, Assam, India.jpg"
    ),
    (91, "Puri", "Jagannath Temple, Puri, Odisha.jpg"),
    (
        93,
        "Konark",
        "13th Century sculptures at Konark Sun Temple Puri district, Odisha, India.jpg"
    ),
    (95, "Khajuraho", "Khajuraho Group of Monuments 5.jpg"),
]


def clean_html(value):
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def get_commons_metadata(filenames):
    titles = "|".join("File:" + name for name in filenames)

    params = {
        "action": "query",
        "format": "json",
        "formatversion": "2",
        "titles": titles,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": "960",
    }

    response = requests.get(
        API_URL,
        params=params,
        headers=HEADERS,
        timeout=(20, 90),
    )
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    pages = data.get("query", {}).get("pages", [])

    result = {}

    for page in pages:
        title = page.get("title", "")
        imageinfo = page.get("imageinfo", [])

        if not imageinfo:
            result[title] = {
                "error": "File does not exist or has no image information."
            }
            continue

        info = imageinfo[0]
        metadata = info.get("extmetadata", {})

        def field(name):
            return clean_html(
                metadata.get(name, {}).get("value", "")
            )

        license_name = field("LicenseShortName")
        artist = field("Artist")
        credit = field("Credit")
        license_url = field("LicenseUrl")

        result[title] = {
            "image_url": info.get("thumburl") or info.get("url"),
            "source_url": info.get("descriptionurl"),
            "creator": artist,
            "credit": credit,
            "license": license_name,
            "license_url": license_url,
            "error": None,
        }

    return result


def reusable_license(name):
    value = name.lower()

    if "noncommercial" in value or "non-commercial" in value:
        return False

    if "no derivatives" in value or "no-derivatives" in value:
        return False

    allowed = (
        "cc0",
        "cc by",
        "cc-by",
        "public domain",
        "pd ",
    )

    return any(item in value for item in allowed)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply verified image updates to MySQL."
    )
    args = parser.parse_args()

    filenames = [item[2] for item in DESTINATIONS]

    print("\nChecking Wikimedia Commons file pages...")
    print("Please wait; no database changes are being made.")

    try:
        commons_data = get_commons_metadata(filenames)
    except Exception as error:
        print("\nCould not verify Wikimedia files:", error)
        print("No database changes have been made.")
        return

    verified = []
    failed = []

    print("\nWIKIMEDIA IMAGE VERIFICATION")
    print("--------------------------------")

    for destination_id, name, filename in DESTINATIONS:
        page_title = "File:" + filename

        info = commons_data.get(page_title)

        if not info or info.get("error"):
            print(f"\nFAILED: {name} (ID {destination_id})")
            print("File:", filename)
            print(info.get("error") if info else "File not returned by Commons.")
            failed.append(name)
            continue

        if not info["image_url"] or not info["source_url"]:
            print(f"\nFAILED: Missing image/source URL for {name}")
            failed.append(name)
            continue

        if not info["license"] or not reusable_license(info["license"]):
            print(f"\nFAILED: Licence needs review for {name}")
            print("Actual licence:", info["license"] or "Not provided")
            failed.append(name)
            continue

        if not info["creator"]:
            print(f"\nFAILED: Creator information missing for {name}")
            failed.append(name)
            continue

        verified.append({
            "id": destination_id,
            "name": name,
            "filename": filename,
            **info,
        })

        print(f"\nVERIFIED: {name} (ID {destination_id})")
        print("File:", filename)
        print("Creator:", info["creator"])
        print("Licence:", info["license"])
        print("Licence URL:", info["license_url"])
        print("Image URL:", info["image_url"])
        print("Source URL:", info["source_url"])

    print("\n--------------------------------")
    print("Verified files:", len(verified))
    print("Files needing attention:", len(failed))

    if failed:
        print("\nSTOP: Some files need correction.")
        print("No database changes have been made.")
        return

    connection = get_db_connection()

    if connection is None:
        print("\nDatabase connection failed.")
        return

    cursor = connection.cursor()

    try:
        ids = [item[0] for item in DESTINATIONS]
        placeholders = ", ".join(["%s"] * len(ids))

        cursor.execute(
            f"""
            SELECT id, name
            FROM destinations
            WHERE id IN ({placeholders})
            ORDER BY id
            """,
            tuple(ids)
        )

        rows = cursor.fetchall()

        actual = {int(row[0]): row[1] for row in rows}
        expected = {item[0]: item[1] for item in DESTINATIONS}

        if actual != expected:
            print("\nDatabase ID/name verification failed.")
            print("No updates made.")
            return

        if not args.apply:
            print("\nPREVIEW ONLY.")
            print("All files and destination records verified.")
            print("No database changes have been made.")
            print("\nRun with --apply after reviewing this output.")
            return

        # Backup the existing image fields for these 15 records.
        cursor.execute(
            f"""
            CREATE TABLE destinations_images_backup_20261106 AS
            SELECT
                id,
                name,
                image_url,
                image_credit,
                image_license,
                image_source_url
            FROM destinations
            WHERE id IN ({placeholders})
            """,
            tuple(ids)
        )

        for item in verified:
            creator = item["creator"]
            credit = item["credit"] or creator

            cursor.execute(
                """
                UPDATE destinations
                SET
                    image_url = %s,
                    image_credit = %s,
                    image_license = %s,
                    image_source_url = %s
                WHERE id = %s AND name = %s
                """,
                (
                    item["image_url"],
                    credit,
                    item["license"],
                    item["source_url"],
                    item["id"],
                    item["name"],
                )
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    f"Unexpected update count for {item['name']}"
                )

        connection.commit()

        cursor.execute("SELECT COUNT(*) FROM destinations")
        total = cursor.fetchone()[0]

        print("\nSUCCESS!")
        print("Updated image records:", len(verified))
        print("Total destinations:", total)
        print("Other destination fields were not changed.")
        print("Backup: destinations_images_backup_20261106")

    except Exception as error:
        connection.rollback()
        print("\nERROR:", error)
        traceback.print_exc()
        print("Transaction rolled back.")

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()