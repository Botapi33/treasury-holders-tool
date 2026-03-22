import json
import re
from datetime import datetime, timezone
from urllib.request import urlopen

URL = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt"

EXCLUDED_ROWS = {
    "grand total",
    "of which: foreign official",
    "of which: foreign official t-bonds & notes",
    "all other"
}

def fetch_data():
    with urlopen(URL) as response:
        return response.read().decode("utf-8", errors="replace")

def is_number(value: str) -> bool:
    return re.match(r"^-?\d+(\.\d+)?$", value) is not None

def parse_data(raw):
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    header = next((line for line in lines if re.match(r"^Country\s+\d{4}-\d{2}", line)), None)
    if not header:
        raise Exception("Header not found in Treasury file.")

    months = header.split()[1:]
    if len(months) < 2:
        raise Exception("Could not detect latest and prior month.")

    latest_month = months[0]
    prior_month = months[1]

    rows = []

    for line in lines:
        if line.startswith("Country "):
            continue
        if line.lower().startswith("table "):
            continue
        if line.lower().startswith("holdings"):
            continue
        if line.lower().startswith("billions"):
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        numbers = []
        while parts and is_number(parts[-1]):
            numbers.insert(0, parts.pop())

        if len(numbers) < 2:
            continue

        country = " ".join(parts).strip()
        if not country:
            continue

        country_lower = country.lower()
        if country_lower in EXCLUDED_ROWS:
            continue

        current = float(numbers[0])
        prior_val = float(numbers[1])

        rows.append({
            "country": country,
            "current": current,
            "prior": prior_val
        })

    rows.sort(key=lambda x: x["current"], reverse=True)

    if not rows:
        raise Exception("No valid country rows were parsed.")

    return {
        "meta": {
            "title": "Major Foreign Holders of U.S. Treasury Securities",
            "source": "U.S. Treasury TIC",
            "frequency": "Monthly",
            "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reportMonth": latest_month,
            "priorMonth": prior_month
        },
        "holders": rows[:20]
    }

def save_json(data):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print("Fetching Treasury data...")
    raw = fetch_data()

    print("Parsing data...")
    parsed = parse_data(raw)

    print("Saving data.json...")
    save_json(parsed)

    print("Done.")
    print(f"Latest month: {parsed['meta']['reportMonth']}")
    print(f"Top holder: {parsed['holders'][0]['country']}")

if __name__ == "__main__":
    main()
