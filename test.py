import requests

username = "corentin_mrchd"
url = f"https://api.chess.com/pub/player/{username}/games/2025/04"
headers = {'User-Agent': 'Mozilla/5.0'}

response = requests.get(url, headers=headers)  # <-- headers ajoutés ici

if response.status_code == 200:
    data = response.json()
    for game in data.get("games", []):
        print(game["url"])
else:
    print(f"Erreur {response.status_code}")
