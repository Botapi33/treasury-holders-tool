import json
import re
from datetime import datetime, timezone
from urllib.request import urlopen

URL = "https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table5.txt"

def fetch_data():
    with urlopen(URL) as response:
        return response.read().decode("utf-8", errors="replace")

def parse_data(raw):
    lines = [line.strip() for line in raw.splitlines() if line.strip()]

    # Header finden (enthält Monate)
    header = next((l for l in lines if re.match(r"^Country\s+\d{4}-\d{2}", l)), None)
    if not header:
        raise Exception("Header nicht gefunden")

    months = header.split()[1:]
    latest = months[0]
    prior = months[1]

    rows = []

    for line in lines:
        if line.startswith("Country "):
            continue
        if "Table" in line:
            continue
        if "Holdings" in line:
            continue
        if "Billions" in line:
            continue

        parts = line.split()
        if len(parts) < 3:
            continue

        numbers = []
        while parts and re.match(r"^-?\d+(\.\d+)?$", parts[-1]):
            numbers.insert(0, parts.pop())

        if len(numbers) < 2:
            continue

        country = " ".join(parts)
        current = float(numbers[0])
        prior_val = float(numbers[1])

        rows.append({
            "country": country,
            "current": current,
            "prior": prior_val
        })

    # Sortieren
    rows.sort(key=lambda x: x["current"], reverse=True)

    return {
        "meta": {
            "title": "Major Foreign Holders of U.S. Treasury Securities",
            "source": "U.S. Treasury TIC",
            "frequency": "Monthly",
            "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "reportMonth": latest,
            "priorMonth": prior
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

    print("Done ✅")
    print(f"Latest month: {parsed['meta']['reportMonth']}")
    print(f"Top holder: {parsed['holders'][0]['country']}")

if __name__ == "__main__":
    main()
