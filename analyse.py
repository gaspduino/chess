import os
import requests
import chess.pgn
import chess.engine
import io

def get_latest_game_pgn(username, year, month):
    url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
    
    # Ajout de headers pour simuler une requête plus authentique
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive'
    }
    
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        games = response.json().get("games", [])
        if games:
            last_game = games[-1]  # dernière partie
            return last_game
        else:
            print("Aucune partie trouvée pour ce mois.")
            return None
    else:
        print(f"Erreur {response.status_code} lors de la récupération.")
        return None

def evaluate_move(score):
    if score is None:
        return "Pas d'évaluation"
    if score >= 500:
        return "Brilliant"
    elif 200 <= score < 500:
        return "Very good"
    elif 100 <= score < 200:
        return "Best"
    elif 50 <= score < 100:
        return "Excellent"
    elif 20 <= score < 50:
        return "Good"
    elif 0 <= score < 20:
        return "Theoretical Inaccuracy"
    elif -20 < score < 0:
        return "Mistake"
    elif -50 < score <= -20:
        return "Blunder"
    else:
        return "Blunder"

def save_analysis_to_txt(analysis_text, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Crée le dossier s'il n'existe pas
    with open(file_path, "w") as file:
        file.write(analysis_text)
    print(f"Analyse enregistrée dans {file_path}")

# Tes infos
username = "corentin_mrchd"
year = 2025
month = 4

game_data = get_latest_game_pgn(username, year, month)

if game_data:
    pgn_data = game_data.get("pgn")
    white_player = game_data.get("white", {}).get("username", "Unknown White")
    black_player = game_data.get("black", {}).get("username", "Unknown Black")

    game = chess.pgn.read_game(io.StringIO(pgn_data))

    analysis_text = ""
    
    with chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish") as engine:
        board = game.board()

        for move in game.mainline_moves():
            move_san = board.san(move)
            analysis_text += f"Coup joué : {move_san}\n"
            board.push(move)

            info = engine.analyse(board, chess.engine.Limit(time=1.0))
            score_obj = info["score"].relative

            if score_obj.is_mate():
                analysis_text += f"Évaluation : Mat en {score_obj.mate()}\n"
                analysis_text += "Évaluation du coup : Forced Mate\n"
            else:
                evaluation = score_obj.score(mate_score=10000)
                analysis_text += f"Évaluation : {evaluation}\n"
                analysis_text += f"Évaluation du coup : {evaluate_move(evaluation)}\n"

            if "pv" in info:
                best_move = info["pv"][0]
                analysis_text += f"Meilleur coup : {board.san(best_move)}\n"
            else:
                analysis_text += "Aucun meilleur coup trouvé.\n"
            analysis_text += "\n"

    # Générer le chemin du fichier en utilisant les noms des joueurs
    file_name = f"{white_player}_vs_{black_player}_game_analysis.txt"
    file_path = f"/home/gaspard/Documents/code/python/chess/chess/analyses/{file_name}"

    # Enregistrer l'analyse dans un fichier texte
    save_analysis_to_txt(analysis_text, file_path)
