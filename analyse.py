import tkinter as tk
import chess
import chess.svg
import chess.pgn
import chess.engine
from cairosvg import svg2png
from PIL import Image, ImageTk
import io
import os
import tkinter.messagebox

# === Configuration du moteur Stockfish ===
try:
    engine = chess.engine.SimpleEngine.popen_uci("/usr/games/stockfish")
except FileNotFoundError:
    tkinter.messagebox.showerror("Erreur", "Stockfish introuvable à /usr/games/stockfish. Veuillez vérifier l'installation.")
    raise

ENGINE_TIME = 1.0  # Temps d'analyse par coup en secondes (augmenté pour plus de précision)

# === Trouver le dernier fichier PGN ===
analyses_folder = "analyses"
pgn_files = [f for f in os.listdir(analyses_folder) if f.endswith(".pgn")]
pgn_files.sort(key=lambda x: os.path.getmtime(os.path.join(analyses_folder, x)), reverse=True)

if not pgn_files:
    raise FileNotFoundError("Aucun fichier PGN trouvé dans le dossier 'analyses/'.")

latest_file = os.path.join(analyses_folder, pgn_files[0])

# === Lecture du PGN avec chess.pgn ===
with open(latest_file, "r") as f:
    game = chess.pgn.read_game(f)

if not game:
    raise ValueError("Le fichier PGN ne contient pas de partie valide.")

# === Analyse des coups ===
def analyze_moves(game):
    board = game.board()
    move_evaluations = []
    
    for move in game.mainline_moves():
        info = engine.analyse(board, chess.engine.Limit(time=ENGINE_TIME))
        best_move = info["pv"][0] if "pv" in info else None
        best_score = info["score"].relative.score(mate_score=10000) or 0
        
        board.push(move)
        
        info_after = engine.analyse(board, chess.engine.Limit(time=ENGINE_TIME))
        after_score = info_after["score"].relative.score(mate_score=10000) or 0
        
        if board.turn == chess.BLACK:
            loss = best_score - after_score
        else:
            loss = after_score - best_score
        
        # Seuils indulgents
        if loss <= 20:
            quality = "excellent"
            emoji = "✅"
            symbol = "!!"
        elif loss <= 100:
            quality = "good"
            emoji = "👍"
            symbol = "!"
        elif loss <= 250:
            quality = "inaccurate"
            emoji = "🤔"
            symbol = "?"
        elif loss <= 500:
            quality = "mistake"
            emoji = "❌"
            symbol = "?!"
        else:
            quality = "blunder"
            emoji = "😱"
            symbol = "??"
            
        move_evaluations.append({
            "move": move,
            "quality": quality,
            "emoji": emoji,
            "symbol": symbol,
            "from_square": move.from_square,
            "to_square": move.to_square,
            "best_move": best_move,
            "best_from_square": best_move.from_square if best_move else None,
            "best_to_square": best_move.to_square if best_move else None
        })
    
    return move_evaluations

# Créer les positions et analyser les coups
board = game.board()
boards = [board.copy()]
move_evaluations = analyze_moves(game)
for move in game.mainline_moves():
    board.push(move)
    boards.append(board.copy())

# === Interface graphique ===
class ChessViewer(tk.Tk):
    def __init__(self, positions, evaluations):
        super().__init__()
        self.positions = positions
        self.evaluations = evaluations
        self.index = 0

        self.title("Visualiseur d'échecs")
        self.geometry("500x500")

        self.canvas = tk.Label(self)
        self.canvas.pack()

        self.move_label = tk.Label(self, text="", font=("Arial", 12))
        self.move_label.pack()

        controls = tk.Frame(self)
        controls.pack()

        tk.Button(controls, text="⏮️", command=self.first).pack(side="left")
        tk.Button(controls, text="◀️", command=self.prev).pack(side="left")
        tk.Button(controls, text="▶️", command=self.next).pack(side="left")
        tk.Button(controls, text="⏭️", command=self.last).pack(side="left")

        self.show()

    def show(self):
        move_text = ""
        arrows = []
        
        # Ajouter une flèche verte pour le meilleur coup (plus fine)
        if self.index < len(self.positions) - 1:
            eval_info = self.evaluations[self.index]
            if eval_info["best_move"]:
                arrows.append(
                    chess.svg.Arrow(
                        eval_info["best_from_square"],
                        eval_info["best_to_square"],
                        color="#00FF00AA"  # Vert avec transparence pour une flèche plus fine
                    )
                )
        
        svg = chess.svg.board(
            self.positions[self.index],
            arrows=arrows,
            size=350,
            colors={
                "square light": "#EEEDD5",  # Couleur claire (comme Chess.com)
                "square dark": "#739552",   # Couleur foncée (comme Chess.com)
                "margin": "#00000000",      # Pas de bordure
                "coord": "#000000",         # Couleur des coordonnées
            }
        )
        
        # Mettre en évidence les cases de départ et d'arrivée
        if self.index > 0:
            eval_info = self.evaluations[self.index - 1]
            from_square = eval_info["from_square"]
            to_square = eval_info["to_square"]
            from_file = chess.square_file(from_square)
            from_rank = 7 - chess.square_rank(from_square)
            to_file = chess.square_file(to_square)
            to_rank = 7 - chess.square_rank(to_square)
            # Ajouter une couleur de fond vert clair pour les cases
            svg = svg.replace(
                f'<rect x="{from_file * 45}" y="{from_rank * 45}" width="45" height="45"',
                f'<rect x="{from_file * 45}" y="{from_rank * 45}" width="45" height="45" fill="#90EE90"/>'
            )
            svg = svg.replace(
                f'<rect x="{to_file * 45}" y="{to_rank * 45}" width="45" height="45"',
                f'<rect x="{to_file * 45}" y="{to_rank * 45}" width="45" height="45" fill="#90EE90"/>'
            )
        
        # Ajouter un émoji pour le coup joué (plus petit et mieux centré)
        if self.index > 0:
            eval_info = self.evaluations[self.index - 1]
            to_square = eval_info["to_square"]
            file = chess.square_file(to_square)
            rank = 7 - chess.square_rank(to_square)
            x = file * 45 + 22.5
            y = rank * 45 + 15  # Décalage vers le haut pour mieux centrer
            svg = svg.replace(
                '</svg>',
                f'<text x="{x}" y="{y}" font-size="15" font-family="Noto Color Emoji, Arial" text-anchor="middle">{eval_info["emoji"]}</text></svg>'
            )
            print(f"SVG modifié pour coup {eval_info['move']}: {eval_info['emoji']} à x={x}, y={y}")
            move_text = f"Coup: {eval_info['move']} ({eval_info['quality'].capitalize()})"
        
        try:
            png_data = svg2png(bytestring=svg)
            image = Image.open(io.BytesIO(png_data))
            self.img = ImageTk.PhotoImage(image)
            self.canvas.config(image=self.img)
        except Exception as e:
            print(f"Erreur lors de la conversion SVG: {e}")
            svg = svg.replace(
                '</svg>',
                f'<text x="{x}" y="{y}" font-size="12" font-family="Arial" text-anchor="middle">{eval_info["symbol"]}</text></svg>'
            )
            png_data = svg2png(bytestring=svg)
            image = Image.open(io.BytesIO(png_data))
            self.img = ImageTk.PhotoImage(image)
            self.canvas.config(image=self.img)
        
        self.move_label.config(text=move_text)

    def next(self):
        if self.index < len(self.positions) - 1:
            self.index += 1
            self.show()

    def prev(self):
        if self.index > 0:
            self.index -= 1
            self.show()

    def first(self):
        self.index = 0
        self.show()

    def last(self):
        self.index = len(self.positions) - 1
        self.show()

    def destroy(self):
        engine.quit()
        super().destroy()

if __name__ == "__main__":
    app = ChessViewer(boards, move_evaluations)
    app.mainloop()
    