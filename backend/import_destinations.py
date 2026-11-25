
import json
import re
import time
import argparse
from pathlib import Path
from urllib.parse import unquote

import requests
from dotenv import load_dotenv

# --------------------------------------------------
# PROJECT CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

load_dotenv(PROJECT_DIR / ".env")

PREVIEW_FILE = BASE_DIR / "destination_import_preview.json"

WIKIDATA_URL = "https://query.wikidata.org/sparql"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "WaymateTravelProject/1.0 "
        "(https://github.com/kshitijapujare03/Waymate)"
    )
}
CLASSES = """
Q515
Q3957
Q570116
Q46169
Q8502
Q23397
Q23442
Q44539
Q57821
Q40080
"""

# Request throttling: minimum 1 second between API requests.
LAST_REQUEST_TIME = 0
REQUEST_DELAY = 1.0



def build_sparql_query(class_id):
    return f"""
    SELECT DISTINCT ?place ?placeLabel ?coord ?classLabel
           ?adminLabel ?article ?sitelinks
    WHERE {{
        ?place wdt:P17 wd:Q668;
               wdt:P625 ?coord;
               wdt:P31 wd:{class_id}.

        BIND(wd:{class_id} AS ?class)

        ?place wikibase:sitelinks ?sitelinks.
        FILTER(?sitelinks >= 3)

        ?article schema:about ?place;
                 schema:isPartOf <https://en.wikipedia.org/>.

        OPTIONAL {{
            ?place wdt:P131 ?admin.
            ?admin rdfs:label ?adminLabel.
            FILTER(LANG(?adminLabel) = "en")
        }}

        SERVICE wikibase:label {{
            bd:serviceParam wikibase:language "en".
        }}
    }}
    LIMIT 15
    """



# --------------------------------------------------
# HTTP REQUESTS WITH RETRIES
# --------------------------------------------------

def get_json(url, params=None):
    global LAST_REQUEST_TIME

    max_attempts = 3

    for attempt in range(max_attempts):

        # Respect the minimum delay between requests.
        elapsed = time.time() - LAST_REQUEST_TIME

        if elapsed < REQUEST_DELAY:
            time.sleep(REQUEST_DELAY - elapsed)

        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=(15, 30)
            )

            LAST_REQUEST_TIME = time.time()

            # Retry temporary server errors and rate limits.
            if response.status_code in (429, 500, 502, 503, 504):

                retry_after = response.headers.get("Retry-After")

                try:
                    wait_time = float(retry_after) if retry_after else 3 * (attempt + 1)
                except ValueError:
                    wait_time = 3 * (attempt + 1)

                wait_time = min(wait_time, 30)

                print(
                    f"Temporary API error: HTTP {response.status_code}"
                )

                if attempt == max_attempts - 1:
                    response.raise_for_status()

                print(f"Retrying in {wait_time:.0f} seconds...")
                time.sleep(wait_time)
                continue

            # Do not retry permanent HTTP errors.
            response.raise_for_status()

            return response.json()

        except (requests.Timeout, requests.ConnectionError) as error:

            LAST_REQUEST_TIME = time.time()

            print(
                f"Connection attempt "
                f"{attempt + 1}/{max_attempts} failed: {error}"
            )

            if attempt == max_attempts - 1:
                print("Request failed. Skipping this API request.")
                raise

            wait_time = 3 * (attempt + 1)

            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    raise requests.RequestException(
        "API request failed after all retry attempts."
    )


def query_wikidata():
    global LAST_REQUEST_TIME

    class_ids = list(dict.fromkeys(re.findall(r"Q\d+", CLASSES)))

    if not class_ids:
        raise ValueError("No Wikidata class IDs found in CLASSES.")

    all_bindings = []
    successful_queries = 0

    max_attempts = 5

    print("Wikidata categories to check:", len(class_ids))

    for class_index, class_id in enumerate(class_ids, start=1):

        print(
            f"\nChecking category {class_index}/{len(class_ids)}: "
            f"{class_id}"
        )

        query = build_sparql_query(class_id)
        class_success = False

        for attempt in range(max_attempts):

            # Respect the delay between API requests.
            elapsed = time.time() - LAST_REQUEST_TIME

            if elapsed < REQUEST_DELAY:
                time.sleep(REQUEST_DELAY - elapsed)

            try:
                response = requests.post(
                    WIKIDATA_URL,
                    data={
                        "query": query,
                        "format": "json"
                    },
                    headers={
                        **HEADERS,
                        "Accept": "application/sparql-results+json"
                    },
                    timeout=(15, 90)
                )

                LAST_REQUEST_TIME = time.time()

                # Retry temporary server errors and rate limits.
                if response.status_code in (429, 500, 502, 503, 504):

                    retry_after = response.headers.get("Retry-After")

                    try:
                        wait_time = float(retry_after) if retry_after else 5 * (attempt + 1)
                    except ValueError:
                        wait_time = 5 * (attempt + 1)

                    wait_time = min(wait_time, 60)

                    print(
                        f"Wikidata temporarily unavailable "
                        f"(HTTP {response.status_code})."
                    )

                    if attempt == max_attempts - 1:
                        response.raise_for_status()

                    print(f"Retrying in {wait_time:.0f} seconds...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()

                bindings = data.get(
                    "results", {}
                ).get("bindings", [])

                all_bindings.extend(bindings)

                successful_queries += 1
                class_success = True

                print(
                    f"Found {len(bindings)} candidates "
                    f"for {class_id}"
                )

                break

            except (requests.Timeout, requests.ConnectionError) as error:

                print(
                    f"Connection attempt {attempt + 1}/{max_attempts} "
                    f"failed for {class_id}: {error}"
                )

                if attempt == max_attempts - 1:
                    break

                wait_time = 5 * (attempt + 1)

                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)

            except requests.HTTPError as error:

                print(f"HTTP error for {class_id}: {error}")
                break

        if not class_success:
            print(
                f"Skipping category {class_id} "
                "because Wikidata did not respond."
            )

        # Pause between category queries.
        time.sleep(2)

    if successful_queries == 0:
        raise RuntimeError(
            "All Wikidata category requests failed. "
            "No destination data was collected."
        )

    print("\nSuccessful category queries:", successful_queries)
    print("Total candidates collected:", len(all_bindings))

    return {
        "results": {
            "bindings": all_bindings
        }
    }


# --------------------------------------------------
# DESTINATION HELPERS
# --------------------------------------------------



def destination_category(class_name):
    value = (class_name or "").lower().strip()

    # 1. Beach
    if any(word in value for word in [
        "beach", "coastal", "coastline", "coast",
        "seaside", "shore"
    ]):
        return "Beach"

    # 2. Mountain
    if any(word in value for word in [
        "mountain", "mountain range", "peak",
        "hill", "himalaya", "mountain pass",
        "glacier"
    ]):
        return "Mountain"

    # 3. Religious
    if any(word in value for word in [
        "temple", "religious", "pilgrimage",
        "mosque", "church", "monastery",
        "shrine", "gurudwara", "stupa",
        "sacred site"
    ]):
        return "Religious"

    # 4. Nature
    if any(word in value for word in [
        "national park", "wildlife sanctuary",
        "nature reserve", "wetland", "lake",
        "river", "waterfall", "forest", "island",
        "biosphere reserve", "protected area",
        "tiger reserve", "valley", "cave"
    ]):
        return "Nature"

    # 5. Heritage
    if any(word in value for word in [
        "fort", "heritage", "historic", "historical",
        "monument", "archaeological", "palace",
        "museum", "city", "town", "human settlement",
        "municipality", "urban settlement",
        "village", "capital", "settlement"
    ]):
        return "Heritage"

    # Default category for unrecognized Wikidata classes
    return "Other"





def recommended_days(category):
    return {
        "Beach": 3,
        "Mountain": 4,
        "Heritage": 2,
        "Nature": 3,
        "Religious": 2,
        "Adventure": 3,
        "Other": 2
    }.get(category, 2)


def packing_list(category):
    common = (
        "ID proof, comfortable clothes, toiletries, "
        "medicines, power bank"
    )

    extras = {
        "Beach": "swimwear, sunscreen, sunglasses, slippers",
        "Mountain": "warm clothes, trekking shoes, socks, sunscreen",
        "Heritage": "walking shoes, cap, sunscreen, water bottle",
        "Nature": "walking shoes, insect repellent, raincoat, water bottle",
        "Religious": "modest clothing, comfortable footwear, water bottle",
        "Adventure": "sportswear, trekking shoes, quick-dry clothes, sunscreen, water bottle",
        "Other": "walking shoes, water bottle, personal essentials, camera"
    }

    return common + ", " + extras.get(
        category, "comfortable shoes, water bottle"
    )



def coordinates_from_wkt(wkt):
    match = re.search(
        r"Point\(\s*([-0-9.]+)\s+([-0-9.]+)\s*\)",
        wkt
    )

    if not match:
        return None, None

    longitude = float(match.group(1))
    latitude = float(match.group(2))

    return latitude, longitude


def clean_html(value):
    if not value:
        return None

    return re.sub(r"<[^>]+>", "", value).strip()


# --------------------------------------------------
# WIKIPEDIA AND IMAGE INFORMATION
# --------------------------------------------------




def get_commons_image_info(file_title):
    params = {
        "action": "query",
        "format": "json",
        "prop": "imageinfo",
        "iiprop": "url|extmetadata",
        "iiurlwidth": 900,
        "titles": file_title
    }

    try:
        data = get_json(WIKIPEDIA_API, params)

        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})
        image_info = page.get("imageinfo", [])

        if not image_info:
            return None

        info = image_info[0]
        metadata = info.get("extmetadata", {})

        image_url = info.get("thumburl") or info.get("url")
        source_url = info.get("descriptionurl")

        license_name = clean_html(
            metadata.get("LicenseShortName", {}).get("value", "")
        )

        license_url = metadata.get(
            "LicenseUrl", {}
        ).get("value", "")

        artist = clean_html(
            metadata.get("Artist", {}).get("value", "")
        )

        # Image URL and source are compulsory.
        if not image_url or not source_url:
            return None

        # Licence information is compulsory.
        if not license_name or not license_url:
            return None

        # Allow missing creator credit only for licences
        # that generally do not require attribution.
        if not artist:
            license_lower = license_name.lower()

            no_attribution_required = (
                "cc0" in license_lower
                or "public domain" in license_lower
            )

            if not no_attribution_required:
                return None

            artist = "No attribution required"

        return {
            "image_url": image_url,
            "image_credit": artist,
            "image_license": license_name,
            "image_source_url": source_url
        }

    except requests.RequestException as error:
        print(f"Image metadata request failed: {error}")
        return None







def get_wikipedia_details(article_url):
    title = unquote(article_url.rstrip("/").split("/")[-1])

    description = None
    image_data = None

    try:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|pageimages",
            "exintro": 1,
            "explaintext": 1,
            "piprop": "thumbnail|name",
            "pithumbsize": 900,
            "titles": title
        }

        data = get_json(WIKIPEDIA_API, params)

        pages = data.get("query", {}).get("pages", {})
        page = next(iter(pages.values()), {})

        if "missing" not in page:
            description = page.get("extract")
            image_name = page.get("pageimage")

            if image_name:
                image_data = get_commons_image_info(
                    "File:" + image_name
                )

    except requests.RequestException as error:
        print(f"Wikipedia request failed for {title}: {error}")

    if not description or not description.strip():
        return None

    
        

    return {
        "description": description.strip()[:5000],
        "image_url": image_data.get("image_url") if image_data else None,
        "image_credit": image_data.get("image_credit") if image_data else None,
        "image_license": image_data.get("image_license") if image_data else None,
        "image_source_url": image_data.get("image_source_url") if image_data else None
    }



# --------------------------------------------------
# COLLECT DESTINATIONS
# --------------------------------------------------

def collect_destinations():
    print("Connecting to Wikidata...")

    result = query_wikidata()

    bindings = result.get(
        "results", {}
    ).get("bindings", [])

    print("Wikidata candidates found:", len(bindings))

    destinations = []
    seen_ids = set()

    for index, item in enumerate(bindings, start=1):

        wikidata_id = item["place"]["value"].rsplit("/", 1)[-1]

        if wikidata_id in seen_ids:
            continue

        seen_ids.add(wikidata_id)

        name = item["placeLabel"]["value"]

        article_url = item.get("article", {}).get("value")

        if not article_url:
            print("Skipped (no Wikipedia article):", name)
            continue

        class_name = item.get(
            "classLabel", {}
        ).get("value", "Nature")

        admin = item.get(
            "adminLabel", {}
        ).get("value", "India")

        sitelinks = int(
            item.get("sitelinks", {}).get("value", 0)
        )

        latitude, longitude = coordinates_from_wkt(
            item["coord"]["value"]
        )

        category = destination_category(class_name)

        print(f"[{index}/{len(bindings)}] Fetching: {name}")

        try:
            details = get_wikipedia_details(article_url)

        except requests.RequestException as error:
            print("Could not fetch Wikipedia data for", name)
            print(error)
            continue

        if not details:
            print("Skipped: no usable description for", name)
            continue

        destinations.append({
            "name": name,
            "location": (
                admin + ", India" if admin != "India" else "India"
            ),
            "destination_type": category,
            "description": details["description"],
            "weather": None,
            "packing_essentials": packing_list(category),
            "rating": None,
            "image_url": details["image_url"],
            "recommended_days": recommended_days(category),
            "latitude": latitude,
            "longitude": longitude,
            "wikidata_id": wikidata_id,
            "description_source_url": article_url,
            "popularity_value": sitelinks,
            "popularity_metric": (
                "Wikidata sitelinks (interest proxy, not visits)"
            ),
            "popularity_source": "Wikidata Query Service",
            "popularity_year": None,
            "image_credit": details["image_credit"],
            "image_license": details["image_license"],
            "image_source_url": details["image_source_url"]
        })

        time.sleep(1.0)

        if len(destinations) >= 70:
            break

    return destinations


# --------------------------------------------------
# PREVIEW MODE - DOES NOT CHANGE MYSQL
# --------------------------------------------------

def preview():
    destinations = collect_destinations()

    with open(PREVIEW_FILE, "w", encoding="utf-8") as file:
        json.dump(
            destinations,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\nPREVIEW COMPLETE")
    print("Destinations collected:", len(destinations))
    print("Preview file:", PREVIEW_FILE)

    if len(destinations) < 70:
        print("NOTICE: Fewer than 70 usable destinations were found.")
        print("We will not invent records to fill the remaining count.")

    print("Your MySQL database has NOT been changed.")


# --------------------------------------------------
# IMPORT PREVIEW INTO MYSQL
# --------------------------------------------------

def import_preview():
    if not PREVIEW_FILE.exists():
        print("Preview file not found. Run --preview first.")
        return

    with open(PREVIEW_FILE, "r", encoding="utf-8") as file:
        destinations = json.load(file)

    if not destinations:
        print("Preview is empty. Nothing to import.")
        return

    from db import get_db_connection

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    inserted = 0
    updated = 0
    skipped = 0

    try:
        cursor.execute(
            "SELECT id, name, wikidata_id FROM destinations"
        )

        existing_rows = cursor.fetchall()

        by_name = {
            row["name"].strip().casefold(): row
            for row in existing_rows
        }

        by_wikidata = {
            row["wikidata_id"]: row
            for row in existing_rows
            if row["wikidata_id"]
        }

        for item in destinations:

            existing = by_wikidata.get(item["wikidata_id"])

            if not existing:
                existing = by_name.get(
                    item["name"].strip().casefold()
                )

            if existing:

                if (
                    existing["wikidata_id"]
                    and existing["wikidata_id"] != item["wikidata_id"]
                ):
                    print("Skipped possible name conflict:", item["name"])
                    skipped += 1
                    continue

                cursor.execute(
                    """
                    
UPDATE destinations SET
    wikidata_id = COALESCE(wikidata_id, %s),
    latitude = COALESCE(latitude, %s),
    longitude = COALESCE(longitude, %s),
    description = IF(
        description IS NULL OR description = '',
        %s, description
    ),
    description_source_url =
        COALESCE(description_source_url, %s),

    image_credit = IF(
        image_url IS NULL OR image_url = '',
        %s, image_credit
    ),
    image_license = IF(
        image_url IS NULL OR image_url = '',
        %s, image_license
    ),
    image_source_url = IF(
        image_url IS NULL OR image_url = '',
        %s, image_source_url
    ),
    image_url = IF(
        image_url IS NULL OR image_url = '',
        %s, image_url
    ),

    popularity_value = COALESCE(popularity_value, %s),
    popularity_metric = COALESCE(popularity_metric, %s),
    popularity_source = COALESCE(popularity_source, %s),
    recommended_days = COALESCE(recommended_days, %s),
    packing_essentials = IF(
        packing_essentials IS NULL
        OR packing_essentials = '',
        %s, packing_essentials
    )
WHERE id = %s

                    """,
                    (
    item["wikidata_id"],
    item["latitude"],
    item["longitude"],
    item["description"],
    item["description_source_url"],
    item["image_credit"],
    item["image_license"],
    item["image_source_url"],
    item["image_url"],
    item["popularity_value"],
    item["popularity_metric"],
    item["popularity_source"],
    item["recommended_days"],
    item["packing_essentials"],
    existing["id"]
)
                )

                updated += 1

            else:

                cursor.execute(
                    """
                    INSERT INTO destinations (
                        name, location, destination_type, description,
                        budget_min, budget_max, weather, packing_essentials,
                        rating, image_url, is_popular, recommended_days,
                        latitude, longitude, wikidata_id,
                        description_source_url, popularity_value,
                        popularity_metric, popularity_source, popularity_year,
                        image_credit, image_license, image_source_url
                    )
                    VALUES (
                        %s, %s, %s, %s,
                        NULL, NULL, NULL, %s,
                        NULL, %s, 0, %s,
                        %s, %s, %s, %s, %s, %s,
                        %s, NULL, %s, %s, %s
                    )
                    """,
                    (
                        item["name"],
                        item["location"],
                        item["destination_type"],
                        item["description"],
                        item["packing_essentials"],
                        item["image_url"],
                        item["recommended_days"],
                        item["latitude"],
                        item["longitude"],
                        item["wikidata_id"],
                        item["description_source_url"],
                        item["popularity_value"],
                        item["popularity_metric"],
                        item["popularity_source"],
                        item["image_credit"],
                        item["image_license"],
                        item["image_source_url"]
                    )
                )

                inserted += 1

                new_id = cursor.lastrowid

                new_record = {
                    "id": new_id,
                    "name": item["name"],
                    "wikidata_id": item["wikidata_id"]
                }

                by_name[item["name"].strip().casefold()] = new_record
                by_wikidata[item["wikidata_id"]] = new_record

        connection.commit()

        print("\nIMPORT COMPLETE")
        print("New destinations inserted:", inserted)
        print("Existing destinations enriched:", updated)
        print("Name conflicts skipped:", skipped)

        cursor.execute(
            "SELECT COUNT(*) AS total FROM destinations"
        )

        print(
            "Total destination records:",
            cursor.fetchone()["total"]
        )

    except Exception:
        connection.rollback()
        print("Import failed. Changes were rolled back.")
        raise

    finally:
        cursor.close()
        connection.close()


# --------------------------------------------------
# COMMAND LINE
# --------------------------------------------------

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Fetch destinations without changing MySQL"
    )

    parser.add_argument(
        "--import-preview",
        action="store_true",
        help="Import the reviewed preview into MySQL"
    )

    args = parser.parse_args()

    if args.preview:
        preview()

    elif args.import_preview:
        import_preview()

    else:
        parser.error("Use --preview or --import-preview")
