"""
Quick correctness test for SQLite migration.
Run from project root: python scripts/test_sqlite.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.carapis_tool import search_all_sources
import sqlite3, datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "inventory.db")

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        print(f"  PASS  {name}")
        PASS += 1
    else:
        print(f"  FAIL  {name} {detail}")
        FAIL += 1

print("\n=== SEARCH TESTS ===")

r = search_all_sources({"make": "Honda", "model": "Civic"})
check("make+model returns results", len(r) > 0)
check("all results are Honda Civic", all(c["make"] == "Honda" and c["model"] == "Civic" for c in r))
check("deal_score present", "deal_score" in r[0])
check("top result has enrichment fields", "safety_rating" in r[0] and "fuel_economy" in r[0])
check("top result has recalls", "recalls" in r[0] and isinstance(r[0]["recalls"], list))
check("2nd result has empty recalls", r[1]["recalls"] == [] if len(r) > 1 else True)
check("results capped at 20", len(r) <= 20)
check("deal_score descending", all(r[i]["deal_score"] >= r[i+1]["deal_score"] for i in range(len(r)-1)))

r2 = search_all_sources({"make": "Honda", "model": "Civic", "budget": 15000})
check("budget filter works", all(c["price"] <= 15000 for c in r2))

r3 = search_all_sources({"make": "Toyota", "year": "2019-2022"})
check("year range filter works", all(2019 <= c["year"] <= 2022 for c in r3))

r4 = search_all_sources({"make": "Honda", "model": "Civic", "year": "2021"})
check("exact year filter works", all(c["year"] == 2021 for c in r4))

r5 = search_all_sources({"make": "Honda", "model": "Civic", "budget": 1000})
check("no match returns empty list", r5 == [])

r6 = search_all_sources({"location": "Phoenix AZ"})
check("location filter works", all("phoenix" in c["location"].lower() for c in r6) if r6 else True)

r7 = search_all_sources({"max_mileage": 20000})
check("mileage filter works", all(c["mileage"] <= 20000 for c in r7))

r8 = search_all_sources({"condition": "used"})
check("condition filter works", all(c["condition"].lower() == "used" for c in r8))

print("\n=== TRADE-IN ESTIMATE TESTS ===")

CONDITION_MAP = {
    "excellent": "excellent_mult", "good": "good_mult",
    "fair": "fair_mult", "poor": "poor_mult", "new": "excellent_mult"
}

def run_estimate(make, model, year, mileage, condition):
    mult_col = CONDITION_MAP.get(condition.strip().lower())
    if not mult_col:
        return {"error": "bad condition"}
    with sqlite3.connect(DB_PATH) as conn:
        rate = conn.execute(
            f"SELECT {mult_col}, market_demand FROM trade_in_rates WHERE LOWER(make)=LOWER(?) AND LOWER(model)=LOWER(?)",
            (make, model)
        ).fetchone()
        if not rate:
            return {"trade_in_value": None, "reasoning": "not in db"}
        avg = conn.execute(
            "SELECT AVG(price), COUNT(*) FROM cars WHERE LOWER(make)=LOWER(?) AND LOWER(model)=LOWER(?) AND year=?",
            (make, model, int(year))
        ).fetchone()
        if not avg or avg[1] == 0:
            avg = conn.execute(
                "SELECT AVG(price), COUNT(*) FROM cars WHERE LOWER(make)=LOWER(?) AND LOWER(model)=LOWER(?) AND year BETWEEN ? AND ?",
                (make, model, int(year)-1, int(year)+1)
            ).fetchone()
    if not avg or avg[1] == 0:
        return {"trade_in_value": None}
    base = float(avg[0])
    mult = float(rate[0])
    num  = int(avg[1])
    curr = datetime.datetime.now().year
    delta = int(mileage) - (curr - int(year)) * 12000
    adj = -(delta / 10000) * 0.02
    val = int(round(base * mult * (1 + adj) / 100) * 100)
    confidence = "high" if num >= 10 else "medium" if num >= 3 else "low"
    return {"trade_in_value": val, "confidence": confidence, "num_matches": num}

e1 = run_estimate("Honda", "Civic", 2020, 35000, "good")
check("Honda Civic estimate returns value", e1.get("trade_in_value") is not None)
check("Honda Civic estimate > 0", (e1.get("trade_in_value") or 0) > 0)
check("confidence level set", e1.get("confidence") in ("low", "medium", "high"))

e2 = run_estimate("Toyota", "Camry", 2019, 40000, "excellent")
check("Toyota Camry estimate returns value", e2.get("trade_in_value") is not None)

e3 = run_estimate("Honda", "Civic", 2020, 35000, "badcondition")
check("bad condition returns error", "error" in e3)

e4 = run_estimate("FakeMake", "FakeModel", 2020, 35000, "good")
check("unknown make/model returns None", e4.get("trade_in_value") is None)

print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed")
if FAIL == 0:
    print("All checks passed — SQLite migration is correct.")
else:
    print("Some checks FAILED — review above.")
