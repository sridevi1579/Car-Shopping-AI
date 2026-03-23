import requests
import sqlite3
import os


NHTSA_BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"
NHTSA_COMPLAINTS = "https://api.nhtsa.gov/complaints/complaintsByVehicle"
NHTSA_RECALLS = "https://api.nhtsa.gov/recalls/recallsByVehicle"
NHTSA_RATINGS = "https://api.nhtsa.gov/SafetyRatings"

def get_real_models(make: str) -> list:
    try:
        r = requests.get(f"{NHTSA_BASE}/GetModelsForMake/{make}?format=json")
        return [m["Model_Name"].lower() for m in r.json()["Results"]]
    except Exception:
        return []

def validate_vehicle(make: str, model: str) -> bool:
    if not make:
        return True
    models = get_real_models(make)
    if not model:
        return len(models) > 0
    return model.lower() in models

# Pool of minor cosmetic/trivial inspection notes for demo purposes
_TRIVIAL_ISSUES = [
    "Minor surface scratches on rear bumper",
    "Small paint chip on driver-side door",
    "Light scuff mark on front bumper",
    "Hairline scratch on trunk lid",
    "Minor door ding on passenger side",
    "Small stone chip on hood",
    "Faint scratch on roof panel",
    "Slight paint fade on side mirror",
]

def _get_trivial_issues(vin: str) -> list:
    """Return 2 unique minor cosmetic notes, varied deterministically by VIN."""
    idx = sum(ord(c) for c in (vin or "")) % len(_TRIVIAL_ISSUES)
    issues = []
    for offset in range(len(_TRIVIAL_ISSUES)):
        issue = _TRIVIAL_ISSUES[(idx + offset) % len(_TRIVIAL_ISSUES)]
        if issue not in issues:
            issues.append(issue)
        if len(issues) == 2:
            break
    return issues

def get_safety_rating(year: int, make: str, model: str) -> str:
    try:
        # Step 1: Get vehicle ID
        r = requests.get(f"{NHTSA_RATINGS}/modelyear/{year}/make/{make}/model/{model}")
        results = r.json().get("Results", [])
        if not results:
            return "N/A"
        
        vehicle_id = results[0].get("VehicleId")
        if not vehicle_id:
            return "N/A"
        
        # Step 2: Get actual rating using vehicle ID
        r2 = requests.get(f"{NHTSA_RATINGS}/VehicleId/{vehicle_id}")
        data = r2.json().get("Results", [])
        if data and data[0].get("OverallRating"):
            rating = data[0]["OverallRating"]
            if rating and rating != "Not Rated":
                return f"{'⭐' * int(rating)} ({rating}/5)"
        return "N/A"
    except Exception:
        return "N/A"

def get_city_from_zip(zip_code: str) -> str:
    try:
        r = requests.get(f"https://api.zippopotam.us/us/{zip_code}")
        data = r.json()
        place = data["places"][0]
        return f"{place['place name']}, {place['state abbreviation']}"
    except Exception:
        return zip_code

FUEL_ECONOMY_BASE = "https://www.fueleconomy.gov/ws/rest"

MODEL_MAP = {
    "Civic": "Civic 4Dr",
    "Accord": "Accord",
    "Camry": "Camry",
    "Corolla": "Corolla",
    "RAV4": "RAV4 4WD",
    "F-150": "F-150",
    "Altima": "Altima",
    "Equinox": "Equinox FWD",
    "CX-5": "CX-5 AWD",
    "Outback": "Outback AWD"
}

def get_fuel_economy(year: int, make: str, model: str) -> str:
    try:
        api_model = MODEL_MAP.get(model, model)
        # Get vehicle options
        r = requests.get(f"{FUEL_ECONOMY_BASE}/vehicle/menu/options?year={year}&make={make}&model={api_model}", headers={"Accept": "application/json"})
        items = r.json().get("menuItem", [])
        if not items:
            return "N/A"
        # Use first option vehicle ID
        vehicle_id = items[0]["value"]
        # Get MPG data
        r2 = requests.get(f"{FUEL_ECONOMY_BASE}/vehicle/{vehicle_id}", headers={"Accept": "application/json"})
        data = r2.json()
        city = data.get("city08", "N/A")
        highway = data.get("highway08", "N/A")
        combined = data.get("comb08", "N/A")
        fuel = data.get("fuelType1", "")
        return f"{city} city / {highway} hwy / {combined} combined MPG ({fuel})"
    except Exception:
        return "N/A"


BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "data", "inventory.db")

def enrich_car(car: dict, include_recalls: bool = False) -> dict:
    """Add NHTSA safety rating, fuel economy, and optionally trivial recall notes to a car."""
    enriched = car.copy()
    enriched["safety_rating"] = get_safety_rating(car["year"], car["make"], car["model"])
    enriched["fuel_economy"] = get_fuel_economy(car["year"], car["make"], car["model"])
    if include_recalls:
        enriched["recalls"] = _get_trivial_issues(car.get("vin", ""))
    else:
        enriched["recalls"] = []
    return enriched

def search_all_sources(filters: dict) -> list:
    make = filters.get("make", "")
    model = filters.get("model", "")
    budget = filters.get("budget", 0)
    max_mileage = filters.get("max_mileage", 0)
    condition = filters.get("condition", "")
    location = filters.get("location", "")

    # Validate with NHTSA
    if make and not validate_vehicle(make, model):
        return []

    # ── Build SQL query dynamically — same filter logic as before ─────────────
    query  = "SELECT source, make, model, year, price, mileage, condition, vin, location, trim, drive_type, color, url FROM cars WHERE 1=1"
    params = []

    if make:
        query += " AND LOWER(make) = LOWER(?)"
        params.append(make)
    if model:
        query += " AND LOWER(model) = LOWER(?)"
        params.append(model)
    if filters.get("year"):
        year_val = filters.get("year")
        if "-" in str(year_val):
            start, end = str(year_val).split("-")
            query += " AND year BETWEEN ? AND ?"
            params.extend([int(start), int(end)])
        else:
            query += " AND year = ?"
            params.append(int(str(year_val)[:4]))
    if budget:
        query += " AND price <= ?"
        params.append(budget)
    if max_mileage:
        query += " AND mileage <= ?"
        params.append(max_mileage)
    if condition:
        query += " AND LOWER(condition) = LOWER(?)"
        params.append(condition)

    skip_locations = {"default", "no preference", "any", "anywhere", ""}
    if location and location.lower() not in skip_locations:
        city = location.lower().replace(", az", "").replace(" az", "").replace(",az", "").replace(",", "").strip()
        query += " AND LOWER(location) LIKE ?"
        params.append(f"%{city}%")

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        results = [dict(r) for r in conn.execute(query, params).fetchall()]



    # Compute best deal score (higher = better deal)
    # Weighted: price 50%, mileage 30%, year 20%
    if results:
        prices   = [c["price"]   for c in results]
        mileages = [c["mileage"] for c in results]
        years    = [int(c["year"]) for c in results]

        min_p, max_p = min(prices),   max(prices)
        min_m, max_m = min(mileages), max(mileages)
        min_y, max_y = min(years),    max(years)

        def deal_score(c):
            np = 1 - ((c["price"]   - min_p) / (max_p - min_p)) if max_p != min_p else 1
            nm = 1 - ((c["mileage"] - min_m) / (max_m - min_m)) if max_m != min_m else 1
            ny =     ((int(c["year"]) - min_y) / (max_y - min_y)) if max_y != min_y else 1
            return 0.5 * np + 0.3 * nm + 0.2 * ny

        for c in results:
            c["deal_score"] = round(deal_score(c), 4)

        results.sort(key=lambda x: x["deal_score"], reverse=True)

    results = results[:20]

    # Enrich top 3 with NHTSA data; only the #1 best deal shows recall notes
    enriched = []
    for i, car in enumerate(results):
        if i == 0:
            enriched.append(enrich_car(car, include_recalls=True))
        elif i < 3:
            enriched.append(enrich_car(car, include_recalls=False))
        else:
            enriched.append(car)

    return enriched