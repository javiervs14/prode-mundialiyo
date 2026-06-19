import requests
from config import Config

headers = {"X-Auth-Token": Config.API_FOOTBALL_KEY}
r = requests.get(f"{Config.API_FOOTBALL_BASE_URL}/competitions/{Config.WC_COMPETITION_ID}/matches", headers=headers)
print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    ms = data.get("matches", [])
    print(f"Matches: {len(ms)}")
    if ms:
        m = ms[0]
        print(f"First: {m.get('utcDate')} - {m.get('homeTeam',{}).get('name')} vs {m.get('awayTeam',{}).get('name')}")
    else:
        print("No matches returned")
elif r.status_code == 429:
    print("Rate limited!")
else:
    print(f"Error: {r.text[:200]}")
