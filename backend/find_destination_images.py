
import requests
import html
import time
import socket
import re
import os

import urllib3.util.connection as urllib3_connection
from html.parser import HTMLParser


# --------------------------------------------------
# CONNECTION SETTINGS
# --------------------------------------------------

# Force IPv4 (the connection workaround tested successfully).
urllib3_connection.allowed_gai_family = lambda: socket.AF_INET

API_URL = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "WaymateTravelProject/1.0 "
        "(https://github.com/kshitijapujare03/Waymate)"
    )
}

# Wait between destination searches.
REQUEST_DELAY = 6

# Number of retries for temporary errors.
MAX_RETRIES = 4

DESTINATIONS = [
    "Varanasi",
    "Udaipur",
    "Jaisalmer",
    "Jodhpur",
    "Darjeeling",
    "Shimla",
    "Nainital",
    "Mysuru",
    "Coorg",
    "Ooty",
    "Munnar",
    "Kaziranga National Park",
    "Puri",
    "Konark",
    "Khajuraho"
]


# --------------------------------------------------
# HTML CLEANING
# --------------------------------------------------

class HTMLTextParser(HTMLParser):

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts).strip()


def clean_html(value):

    if not value:
        return "Not provided"

    parser = HTMLTextParser()

    try:
        parser.feed(str(value))
        return html.unescape(parser.get_text())
    except Exception:
        return str(value)


# --------------------------------------------------
# LICENCE CLASSIFICATION
# --------------------------------------------------

def check_license(metadata):

    license_name = clean_html(
        metadata.get("LicenseShortName", {}).get("value", "")
    )

    license_url = clean_html(
        metadata.get("LicenseUrl", {}).get("value", "")
    )

    normalized = license_name.lower()

    # Missing licence details: retain for manual review.
    if license_name == "Not provided":
        return "MANUAL VERIFICATION REQUIRED"

    # Do not recommend non-commercial or no-derivatives licences.
    restricted_terms = [
        "noncommercial",
        "non-commercial",
        "no derivatives",
        "noderivatives"
    ]

    if any(term in normalized for term in restricted_terms):
        return "DO NOT USE - RESTRICTED LICENCE"

    if re.search(r"(^|[-\s])nc($|[-\s])", normalized):
        return "DO NOT USE - NON-COMMERCIAL"

    if re.search(r"(^|[-\s])nd($|[-\s])", normalized):
        return "DO NOT USE - NO DERIVATIVES"

    # Public domain and CC0.
    if "public domain" in normalized or "cc0" in normalized:
        return "REUSABLE - PUBLIC DOMAIN / CC0"

    # Creative Commons Attribution licences.
    if "cc by" in normalized or "attribution" in normalized:
        if license_url:
            return "REUSABLE - CHECK ATTRIBUTION REQUIREMENTS"

    return "MANUAL VERIFICATION REQUIRED"


# --------------------------------------------------
# REQUEST WITH RETRY HANDLING
# --------------------------------------------------

session = requests.Session()
session.headers.update(HEADERS)


def make_request(params):

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = session.get(
                API_URL,
                params=params,
                timeout=(15, 45)
            )

            if response.status_code == 429:

                retry_after = response.headers.get("Retry-After")

                try:
                    wait_time = int(retry_after)
                except (TypeError, ValueError):
                    wait_time = 20 * attempt

                wait_time = max(wait_time, 10)

                print(
                    f"Rate limited. Waiting {wait_time} seconds "
                    f"(attempt {attempt}/{MAX_RETRIES})..."
                )

                if attempt < MAX_RETRIES:
                    time.sleep(wait_time)
                    continue

            response.raise_for_status()

            return response.json()

        except requests.RequestException as error:

            if attempt == MAX_RETRIES:
                raise

            wait_time = 10 * attempt

            print(
                f"Request failed: {error}\n"
                f"Retrying after {wait_time} seconds..."
            )

            time.sleep(wait_time)

    return {}


# --------------------------------------------------
# IMAGE SEARCH
# --------------------------------------------------

def is_supported_image(page):

    image_info = page.get("imageinfo", [])

    if not image_info:
        return False

    image = image_info[0]

    mime = image.get("mime", "").lower()

    if mime in (
        "image/jpeg",
        "image/png",
        "image/webp"
    ):
        return True

    # Fallback if MIME information is missing.
    title = page.get("title", "").lower()

    return title.endswith((".jpg", ".jpeg", ".png", ".webp"))


def search_images(destination):

    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": destination,
        "gsrnamespace": 6,
        "gsrlimit": 15,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 900,
        "iiextmetadatafilter": (
            "LicenseShortName|LicenseUrl|Artist|Credit|ImageDescription"
        )
    }

    result = make_request(params)

    pages = result.get("query", {}).get("pages", {})

    candidates = []

    for page in pages.values():

        if not is_supported_image(page):
            continue

        image = page["imageinfo"][0]

        metadata = image.get("extmetadata", {})

        artist = clean_html(
            metadata.get("Artist", {}).get("value", "")
        )

        credit = clean_html(
            metadata.get("Credit", {}).get("value", "")
        )

        license_name = clean_html(
            metadata.get("LicenseShortName", {}).get("value", "")
        )

        license_url = clean_html(
            metadata.get("LicenseUrl", {}).get("value", "")
        )

        description = clean_html(
            metadata.get("ImageDescription", {}).get("value", "")
        )

        candidates.append({

            "title": page.get("title", "Not provided"),

            "image_url": (
                image.get("thumburl")
                or image.get("url")
                or "Not provided"
            ),

            "source_url": image.get(
                "descriptionurl",
                "Not provided"
            ),

            "artist": artist,

            "credit": credit,

            "license": license_name,

            "license_url": license_url,

            "description": description,

            "license_status": check_license(metadata)

        })

    return candidates


# --------------------------------------------------
# MAIN PREVIEW
# --------------------------------------------------

def main():

    print("\n" + "=" * 75)
    print("WAYMATE DESTINATION IMAGE DISCOVERY")
    print("Source: Wikimedia Commons")
    print("PREVIEW ONLY - DATABASE WILL NOT BE MODIFIED")
    print("=" * 75)

    total_candidates = 0

    for destination in DESTINATIONS:

        print("\n" + "=" * 75)
        print("DESTINATION:", destination)
        print("=" * 75)

        try:

            candidates = search_images(destination)

            if not candidates:

                print("No matching image candidates found.")

            else:

                total_candidates += len(candidates)

                # Show up to five candidates.
                for index, candidate in enumerate(
                    candidates[:5],
                    start=1
                ):

                    print(f"\nCANDIDATE {index}")

                    print("File:", candidate["title"])

                    print("Image URL:", candidate["image_url"])

                    print("Source page:", candidate["source_url"])

                    print("Creator:", candidate["artist"])

                    print("Credit:", candidate["credit"])

                    print("Licence:", candidate["license"])

                    print("Licence URL:", candidate["license_url"])

                    print(
                        "Licence assessment:",
                        candidate["license_status"]
                    )

                    print("Description:", candidate["description"])

                if len(candidates) > 5:

                    print(
                        f"\n{len(candidates) - 5} more "
                        "candidates not displayed."
                    )

        except requests.RequestException as error:

            print("IMAGE SEARCH FAILED:", error)

        except Exception as error:

            print("UNEXPECTED ERROR:", error)

        # Give Wikimedia time between searches.
        time.sleep(REQUEST_DELAY)

    print("\n" + "=" * 75)
    print("IMAGE DISCOVERY COMPLETED")
    print("Total image candidates found:", total_candidates)
    print("No database records were changed.")
    print("=" * 75)


if __name__ == "__main__":
    main()
