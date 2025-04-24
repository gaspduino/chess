import requests
import os

# Paramètres
username = "corentin_mrchd"  # Joueur Blanc
year = "2025"
month = "04"
game_id = "137711514442"
output_dir = "/home/gaspard/Documents/code/python/chess/mon_app/games"
output_file = os.path.join(output_dir, f"game_{game_id}.pgn")

# Créer le dossier games/ s'il n'existe pas
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# URL de l'API pour récupérer les parties d'un joueur pour un mois donné
url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}"

# Ajouter un en-tête User-Agent pour éviter les blocages
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

try:
    # Faire la requête à l'API
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Vérifier si la requête a réussi

    # Parser la réponse JSON
    data = response.json()

    # Chercher la partie avec l'ID donné
    for game in data.get("games", []):
        game_url = game.get("url", "")
        if game_url.endswith(game_id):
            pgn = game.get("pgn", "")
            if pgn:
                print("PGN trouvé ! Voici le contenu :\n")
                print(pgn)
                
                # Sauvegarder le PGN dans un fichier
                with open(output_file, "w") as f:
                    f.write(pgn)
                print(f"\nPGN sauvegardé dans '{output_file}'")
            else:
                print("PGN non trouvé dans les données de cette partie.")
            break
    else:
        print(f"Partie avec l'ID {game_id} non trouvée dans les archives de {username} pour {year}-{month}.")
        print("Tentative avec l'autre joueur (Corentin_mrchd)...")
        
        # Essayer avec l'autre joueur
        username = "Corentin_mrchd"
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        for game in data.get("games", []):
            game_url = game.get("url", "")
            if game_url.endswith(game_id):
                pgn = game.get("pgn", "")
                if pgn:
                    print("PGN trouvé ! Voici le contenu :\n")
                    print(pgn)
                    
                    # Sauvegarder le PGN dans un fichier
                    with open(output_file, "w") as f:
                        f.write(pgn)
                    print(f"\nPGN sauvegardé dans '{output_file}'")
                else:
                    print("PGN non trouvé dans les données de cette partie.")
                break
        else:
            print(f"Partie avec l'ID {game_id} non trouvée non plus dans les archives de {username} pour {year}-{month}.")

except requests.exceptions.RequestException as e:
    print(f"Erreur lors de la requête à l'API : {e}")