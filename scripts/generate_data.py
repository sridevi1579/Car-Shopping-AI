import csv
import random
import string
import os

random.seed(42)

# ── 12 Models × 10 Cities ─────────────────────────────────────────────────────
CITIES = [
    "Phoenix AZ","Scottsdale AZ","Tempe AZ","Mesa AZ","Chandler AZ",
    "Gilbert AZ","Glendale AZ","Tucson AZ","Surprise AZ","Peoria AZ"
]

COLORS = ["White","Black","Silver","Gray","Blue","Red"]

# (make, model, trims)
MODELS = [
    ("Honda",      "Civic",     ["LX","EX","Sport"]),
    ("Honda",      "Accord",    ["LX","Sport","EX"]),
    ("Honda",      "CR-V",      ["LX","EX","EX-L"]),
    ("Toyota",     "Camry",     ["LE","SE","XSE"]),
    ("Toyota",     "Corolla",   ["LE","SE"]),
    ("Toyota",     "RAV4",      ["LE","XLE","TRD Off-Road"]),
    ("Toyota",     "Tacoma",    ["SR","SR5","TRD Off-Road"]),
    ("Ford",       "F-150",     ["XLT","Lariat"]),
    ("Nissan",     "Altima",    ["S","SV"]),
    ("Nissan",     "Rogue",     ["S","SV","SL"]),
    ("Chevrolet",  "Equinox",   ["LS","LT","Premier"]),
    ("Jeep",       "Wrangler",  ["Sport","Sahara","Rubicon"]),
]
NUM_MODELS = len(MODELS)   # 12

# ── Source/Condition slots per model (sums to 416 → 12 × 416 = 4992 ≈ 5000) ──
SOURCE_SLOTS = [
    ("Carvana",   "used", 138),
    ("Carvana",   "new",    8),
    ("CarMax",    "used", 135),
    ("CarGurus",  "used",  94),
    ("CarGurus",  "new",   41),
]  # 416 per model

USED_YEARS = [2018, 2019, 2020, 2021, 2022]
NEW_YEARS  = [2023, 2024]

USED_PRICE   = {2018:(12000,20000),2019:(14000,22000),2020:(16000,24000),
                2021:(18000,26000),2022:(19000,28000)}
NEW_PRICE    = {2023:(22000,38000),2024:(24000,40000)}
USED_MILEAGE = {2018:(50000,75000),2019:(40000,65000),2020:(30000,50000),
                2021:(20000,40000),2022:(10000,30000)}

TRIM_BUMP = {
    "LX":0,"LE":0,"S":0,"XLT":0,"LS":0,"SR":0,
    "Sport":600,"SE":600,"SV":600,"SR5":800,
    "EX":1200,"XLE":1200,"LT":1200,"Sahara":1500,
    "EX-L":1800,"Lariat":1800,"XSE":1800,"TRD Off-Road":2000,
    "Premier":2200,"SL":2200,"Rubicon":3000,
}

# ── Drive type rules ──────────────────────────────────────────────────────────
def get_drive(model):
    if model == "Wrangler":                        return "4WD"
    if model in ("Tacoma", "F-150"):               return random.choice(["RWD","4WD"])
    if model in ("RAV4","CR-V","Rogue"):            return random.choice(["AWD","AWD","FWD"])
    return "FWD"   # Civic, Accord, Camry, Corolla, Altima, Equinox

# ── VIN generator ─────────────────────────────────────────────────────────────
used_vins: set = set()

def gen_vin():
    while True:
        vin = ''.join(random.choices(string.ascii_uppercase + string.digits, k=17))
        if vin not in used_vins:
            used_vins.add(vin)
            return vin

# ── Row builder ───────────────────────────────────────────────────────────────
def make_row(source, condition, make, model, trim, year, city):
    drive    = get_drive(model)
    awd_bump = 1200 if drive in ("AWD","4WD") else 0
    trim_add = TRIM_BUMP.get(trim, 0)
    src_bump = random.randint(300, 900) if source == "Carvana" else 0

    if condition == "used":
        lo, hi  = USED_PRICE[year]
        price   = random.randint(lo, hi) + trim_add + awd_bump + src_bump
        mlo,mhi = USED_MILEAGE[year]
        mileage = random.randint(mlo, mhi)
    else:
        lo, hi  = NEW_PRICE[year]
        price   = random.randint(lo, hi) + trim_add + awd_bump + src_bump
        mileage = random.randint(5, 50)

    vin  = gen_vin()
    urls = {
        "Carvana":  f"https://www.carvana.com/vehicle/{vin}",
        "CarMax":   f"https://www.carmax.com/car/{vin}",
        "CarGurus": f"https://www.cargurus.com/Cars/inventory/{vin}",
    }
    return {
        "source": source, "make": make, "model": model, "year": year,
        "price": price, "mileage": mileage, "condition": condition,
        "vin": vin, "location": city, "trim": trim,
        "drive_type": drive, "color": random.choice(COLORS), "url": urls[source]
    }

# ── Generate rows ─────────────────────────────────────────────────────────────
rows = []
NUM_CITIES = len(CITIES)

for make, model, trims in MODELS:
    for source, condition, count in SOURCE_SLOTS:
        years = NEW_YEARS if condition == "new" else USED_YEARS
        for i in range(count):
            city = CITIES[i % NUM_CITIES]       # cycle → every city covered equally
            trim = random.choice(trims)
            year = random.choice(years)
            rows.append(make_row(source, condition, make, model, trim, year, city))

random.shuffle(rows)

# ── Write CSV ─────────────────────────────────────────────────────────────────
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cars.csv")
FIELDS = ["source","make","model","year","price","mileage","condition",
          "vin","location","trim","drive_type","color","url"]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

# ── Sanity Report ─────────────────────────────────────────────────────────────
import pandas as pd
df = pd.read_csv(OUT)

print(f"Total rows: {len(df)}")
print()
print("── Model distribution (target ~416 each) ──")
print(df['model'].value_counts().sort_values(ascending=False).to_string())
print()
print("── Source + Condition ──")
print(df.groupby(['source','condition']).size().to_string())
print()
print("── City distribution (target ~499 each) ──")
print(df['location'].value_counts().to_string())
print()
print("── Model × City spread (target ~41 each cell) ──")
pivot = df.groupby(['model','location']).size().unstack(fill_value=0)
print(pivot.to_string())
