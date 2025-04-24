import chess
import chess.pgn
import chess.engine
import os
import datetime
import re

# === Configuration du moteur Stockfish ===
try:
    engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
except FileNotFoundError:
    raise FileNotFoundError("Stockfish introuvable à /usr/games/stockfish. Veuillez vérifier l'installation.")

ENGINE_TIME = 1.0  # Temps d'analyse par coup en secondes

# === Charger le fichier PGN d'entrée ===
game_folder = "games"
# Créer le dossier games/ s'il n'existe pas
if not os.path.exists(game_folder):
    os.makedirs(game_folder)
    print(f"Dossier '{game_folder}' créé. Veuillez y placer un fichier PGN et réexécuter le script.")
    engine.quit()
    exit()

pgn_files = [f for f in os.listdir(game_folder) if f.endswith(".pgn")]
pgn_files.sort(key=lambda x: os.path.getmtime(os.path.join(game_folder, x)), reverse=True)

if not pgn_files:
    raise FileNotFoundError(f"Aucun fichier PGN trouvé dans le dossier '{game_folder}/'. Veuillez y placer un fichier PGN et réexécuter le script.")

latest_game_file = os.path.join(game_folder, pgn_files[0])

with open(latest_game_file, "r") as f:
    game = chess.pgn.read_game(f)

if not game:
    raise ValueError("Le fichier PGN ne contient pas de partie valide.")

# === Récupérer les Elo des joueurs ===
white_elo = game.headers.get("WhiteElo", "1000")
black_elo = game.headers.get("BlackElo", "1000")
try:
    white_elo = int(white_elo)
    black_elo = int(black_elo)
except ValueError:
    white_elo = 1000
    black_elo = 1000

average_elo = (white_elo + black_elo) // 2
print(f"Elo moyen des joueurs : {average_elo}")

# Compter le nombre total de coups pour la progression
total_moves = len(list(game.mainline_moves()))
print(f"Nombre total de coups à analyser : {total_moves}")

# === Définir les seuils en fonction de l'Elo moyen ===
if average_elo < 1000:
    # Très indulgents (débutants)
    THRESHOLDS = {"excellent": 50, "good": 150, "inaccurate": 400, "mistake": 1000, "blunder": float("inf")}
elif average_elo < 1500:
    # Modérés (intermédiaires)
    THRESHOLDS = {"excellent": 40, "good": 120, "inaccurate": 300, "mistake": 700, "blunder": float("inf")}
elif average_elo < 2000:
    # Plus stricts (avancés)
    THRESHOLDS = {"excellent": 30, "good": 100, "inaccurate": 250, "mistake": 500, "blunder": float("inf")}
else:
    # Stricts (experts)
    THRESHOLDS = {"excellent": 20, "good": 80, "inaccurate": 200, "mistake": 400, "blunder": float("inf")}

# === Analyser la partie et annoter les coups ===
def analyze_and_annotate_game(game):
    board = game.board()
    node = game
    move_number = 0
    
    for move in game.mainline_moves():
        move_number += 1
        print(f"Analyse du coup {move_number}/{total_moves} : {move.uci()}")
        
        # Analyser la position avant le coup
        info = engine.analyse(board, chess.engine.Limit(time=ENGINE_TIME))
        best_move = info["pv"][0] if "pv" in info else None
        best_score = info["score"].relative.score(mate_score=10000) or 0
        
        # Jouer le coup
        board.push(move)
        node = node.variation(move)
        
        # Analyser la position après le coup
        info_after = engine.analyse(board, chess.engine.Limit(time=ENGINE_TIME))
        after_score = info_after["score"].relative.score(mate_score=10000) or 0
        
        # Calculer la perte en centipions
        if board.turn == chess.BLACK:  # Après un coup des Blancs
            loss = best_score - after_score
        else:  # Après un coup des Noirs
            loss = after_score - best_score
        
        # Évaluer la qualité du coup
        if loss <= THRESHOLDS["excellent"]:
            quality = "excellent"
            symbol = "!!"
        elif loss <= THRESHOLDS["good"]:
            quality = "good"
            symbol = "!"
        elif loss <= THRESHOLDS["inaccurate"]:
            quality = "inaccurate"
            symbol = "?"
        elif loss <= THRESHOLDS["mistake"]:
            quality = "mistake"
            symbol = "?!"
        else:
            quality = "blunder"
            symbol = "??"
        
        # Créer le commentaire avec la qualité, le symbole et le meilleur coup
        comment = f"[{quality} {symbol}]"
        if best_move and best_move != move:
            comment += f" Meilleur: {best_move.uci()}"
        
        # Nettoyer les annotations existantes (supprimer [%clk ...])
        existing_comment = node.comment if node.comment else ""
        cleaned_comment = re.sub(r"\[%clk [^\]]+\]\s*", "", existing_comment).strip()
        if cleaned_comment:
            node.comment = f"{cleaned_comment} {comment}"
        else:
            node.comment = comment
        print(f"Annotation ajoutée pour {move.uci()}: {node.comment}")  # Débogage

# Analyser et annoter la partie
analyze_and_annotate_game(game)

# === Sauvegarder le PGN annoté dans le dossier analyses/ ===
analyses_folder = "analyses"
if not os.path.exists(analyses_folder):
    os.makedirs(analyses_folder)

# Générer un nom de fichier unique basé sur la date et l'heure
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(analyses_folder, f"analyzed_game_{timestamp}.pgn")

with open(output_file, "w") as f:
    exporter = chess.pgn.FileExporter(f)
    game.accept(exporter)

print(f"Partie analysée et sauvegardée dans : {output_file}")

# Fermer le moteur Stockfish
engine.quit()