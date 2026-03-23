import sys
import os
import json
import datetime
import sqlite3
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastmcp import FastMCP
from tools.carapis_tool import search_all_sources


BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE, "data", "inventory.db")

# Verify DB is accessible at startup
try:
    with sqlite3.connect(DB_PATH) as _conn:
        _car_count  = _conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
        _rate_count = _conn.execute("SELECT COUNT(*) FROM trade_in_rates").fetchone()[0]
    print(f"[MCP] Connected to inventory.db — {_car_count} cars, {_rate_count} trade-in rates")
except Exception as _e:
    print(f"[MCP] ERROR connecting to inventory.db: {_e}")

mcp = FastMCP("Car Agent MCP Server")


class SafeEncoder(json.JSONEncoder):
    """Handle numpy types that aren't JSON serializable by default."""
    def default(self, obj):
        if hasattr(obj, "item"):   # numpy int64, float64, etc.
            return obj.item()
        return super().default(obj)


@mcp.tool()
def search_cars(
    make: str = "",
    model: str = "",
    year: str = "",
    budget: int = 0,
    max_mileage: int = 0,
    condition: str = "",
    location: str = ""
) -> str:
    """
    Search for cars across Carvana, CarMax and CarGurus based on user preferences.
    Returns a JSON array of car results sorted by best deal score.
    """
    filters = {
        "make": make,
        "model": model,
        "year": year,
        "budget": budget,
        "max_mileage": max_mileage,
        "condition": condition,
        "location": location
    }

    results = search_all_sources(filters)

    if not results:
        return json.dumps([])

    return json.dumps(results, cls=SafeEncoder)


# ── Condition → multiplier column mapping ─────────────────────────────────────

CONDITION_MAP = {
    "excellent": "excellent_mult",
    "good":      "good_mult",
    "fair":      "fair_mult",
    "poor":      "poor_mult",
    "new":       "excellent_mult",   # treat "new" car as excellent condition
}


@mcp.tool()
def estimate_trade_in(
    make: str,
    model: str,
    year: int,
    mileage: int,
    condition: str,
    trim: str = "",
    location: str = ""
) -> str:
    """
    Estimate the trade-in value of a user's car.
    Uses market prices from cars.csv and condition multipliers from trade_in_rates.csv.
    Returns a JSON object with trade_in_value, reasoning, financing_impact, and confidence.
    """
    # ── Validate condition input ───────────────────────────────────────────────
    mult_col = CONDITION_MAP.get(condition.strip().lower())
    if not mult_col:
        return json.dumps({
            "trade_in_value": None,
            "reasoning": f"Unknown condition '{condition}'. Please use: Excellent, Good, Fair, or Poor.",
            "financing_impact": "N/A",
            "confidence": "none"
        })

    with sqlite3.connect(DB_PATH) as conn:
        # ── Look up condition multipliers for this make/model ─────────────────
        rate_row = conn.execute(
            f"SELECT {mult_col}, market_demand FROM trade_in_rates "
            "WHERE LOWER(make) = LOWER(?) AND LOWER(model) = LOWER(?)",
            (make.strip(), model.strip())
        ).fetchone()

        if not rate_row:
            return json.dumps({
                "trade_in_value": None,
                "reasoning": f"{make} {model} is not in our trade-in database. Estimate not available.",
                "financing_impact": "N/A",
                "confidence": "none"
            })

        condition_mult = float(rate_row[0])
        market_demand  = str(rate_row[1])

        # ── Get average market price for this make/model/year ─────────────────
        avg_row = conn.execute(
            "SELECT AVG(price), COUNT(*) FROM cars "
            "WHERE LOWER(make) = LOWER(?) AND LOWER(model) = LOWER(?) AND year = ?",
            (make.strip(), model.strip(), int(year))
        ).fetchone()

        if not avg_row or avg_row[1] == 0:
            # Fall back to ±1 year if exact year not found
            avg_row = conn.execute(
                "SELECT AVG(price), COUNT(*) FROM cars "
                "WHERE LOWER(make) = LOWER(?) AND LOWER(model) = LOWER(?) AND year BETWEEN ? AND ?",
                (make.strip(), model.strip(), int(year) - 1, int(year) + 1)
            ).fetchone()

    if not avg_row or avg_row[1] == 0:
        return json.dumps({
            "trade_in_value": None,
            "reasoning": f"No market data found for {year} {make} {model}. Estimate not available.",
            "financing_impact": "N/A",
            "confidence": "low"
        })

    base_value  = float(avg_row[0])
    num_matches = int(avg_row[1])
    confidence = "high" if num_matches >= 10 else "medium" if num_matches >= 3 else "low"

    # ── Mileage adjustment (±2% per 10k miles vs expected) ────────────────────
    current_year    = datetime.datetime.now().year
    expected_miles  = (current_year - int(year)) * 12000
    delta           = int(mileage) - expected_miles              # positive = over expected
    mileage_adj     = -(delta / 10000) * 0.02                   # over by 10k = -2%

    # ── Final trade-in value ───────────────────────────────────────────────────
    raw_value    = base_value * condition_mult * (1 + mileage_adj)
    trade_in_val = int(round(raw_value / 100) * 100)            # round to nearest $100

    # ── Build reasoning sentence ───────────────────────────────────────────────
    miles_note = (
        f"{abs(delta):,} miles under expected — small value boost"
        if delta < 0
        else f"{abs(delta):,} miles over expected — slight reduction"
        if delta > 0
        else "mileage right on expected average"
    )
    demand_note = {
        "very_high": "very high market demand",
        "high":      "high market demand",
        "medium":    "moderate market demand",
        "low":       "lower market demand"
    }.get(market_demand, "market demand unknown")

    reasoning = (
        f"{year} {make} {model} avg market price ${base_value:,.0f} "
        f"({num_matches} listings). "
        f"{condition.capitalize()} condition ({int(condition_mult*100)}% multiplier). "
        f"{miles_note}. {demand_note.capitalize()} in Arizona."
    )

    financing_impact = (
        f"Using this as a down payment reduces your loan amount by ${trade_in_val:,}, "
        f"saving you on interest over the loan term."
    )

    result = {
        "trade_in_value":   trade_in_val,
        "reasoning":        reasoning,
        "financing_impact": financing_impact,
        "confidence":       confidence
    }
    return json.dumps(result, cls=SafeEncoder)


if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=5002)
