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
            return last_game.get("pgn")
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

# Tes infos
username = "corentin_mrchd"
year = 2025
month = 4

pgn_data = get_latest_game_pgn(username, year, month)

if pgn_data:
    game = chess.pgn.read_game(io.StringIO(pgn_data))

    with chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish") as engine:
        board = game.board()

        for move in game.mainline_moves():
            move_san = board.san(move)
            print(f"Coup joué : {move_san}")
            board.push(move)

            info = engine.analyse(board, chess.engine.Limit(time=1.0))
            score_obj = info["score"].relative

            if score_obj.is_mate():
                print(f"Évaluation : Mat en {score_obj.mate()}")
                print("Évaluation du coup : Forced Mate")
            else:
                evaluation = score_obj.score(mate_score=10000)
                print(f"Évaluation : {evaluation}")
                print(f"Évaluation du coup : {evaluate_move(evaluation)}")

            if "pv" in info:
                best_move = info["pv"][0]
                print(f"Meilleur coup : {board.san(best_move)}")
            else:
                print("Aucun meilleur coup trouvé.")
            print()
