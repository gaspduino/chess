import tkinter as tk
import chess
import chess.svg
import chess.pgn
import re
from cairosvg import svg2png
from PIL import Image, ImageTk
import io
import os
import tkinter.messagebox

# === Trouver le dernier fichier PGN ===
analyses_folder = "analyses"
pgn_files = [f for f in os.listdir(analyses_folder) if f.endswith(".pgn")]
pgn_files.sort(key=lambda x: os.path.getmtime(os.path.join(analyses_folder, x)), reverse=True)

if not pgn_files:
    raise FileNotFoundError("Aucun fichier PGN trouvé dans le dossier 'games/'.")

latest_file = os.path.join(analyses_folder, pgn_files[0])

# === Lecture du PGN avec chess.pgn ===
with open(latest_file, "r") as f:
    game = chess.pgn.read_game(f)

if not game:
    raise ValueError("Le fichier PGN ne contient pas de partie valide.")

# === Extraire les évaluations et meilleurs coups depuis les commentaires ===
def extract_evaluations(game):
    board = game.board()
    move_evaluations = []
    node = game
    
    for move in game.mainline_moves():
        board.push(move)
        node = node.variation(move)
        
        # Extraire les informations du commentaire
        comment = node.comment if node.comment else ""
        quality = "unknown"
        symbol = ""
        best_move = None
        
        # Rechercher le motif [quality symbol] et Meilleur: <best_move>
        match = re.match(r"\[(\w+) ([?!]+)\](?:\s*Meilleur:\s*(\w+))?", comment)
        if match:
            quality = match.group(1)  # ex: "mistake"
            symbol = match.group(2)   # ex: "?!"
            if match.group(3):        # Meilleur coup (optionnel)
                best_move = chess.Move.from_uci(match.group(3))
        
        move_evaluations.append({
            "move": move,
            "quality": quality,
            "symbol": symbol,
            "from_square": move.from_square,
            "to_square": move.to_square,
            "best_move": best_move,
            "best_from_square": best_move.from_square if best_move else None,
            "best_to_square": best_move.to_square if best_move else None
        })
    
    return move_evaluations

# Créer les positions et extraire les évaluations
board = game.board()
boards = [board.copy()]
move_evaluations = extract_evaluations(game)
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
        
        # Ajouter une flèche verte pour le meilleur coup
        if self.index < len(self.positions) - 1:
            eval_info = self.evaluations[self.index]
            if eval_info["best_move"]:
                arrows.append(
                    chess.svg.Arrow(
                        eval_info["best_from_square"],
                        eval_info["best_to_square"],
                        color="#00FF00AA"
                    )
                )
        
        svg = chess.svg.board(
            self.positions[self.index],
            arrows=arrows,
            size=350,
            colors={
                "square light": "#EEEDD5",
                "square dark": "#739552",
                "margin": "#00000000",
                "coord": "#000000",
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
            svg = svg.replace(
                f'<rect x="{from_file * 45}" y="{from_rank * 45}" width="45" height="45"',
                f'<rect x="{from_file * 45}" y="{from_rank * 45}" width="45" height="45" fill="#90EE90"/>'
            )
            svg = svg.replace(
                f'<rect x="{to_file * 45}" y="{to_rank * 45}" width="45" height="45"',
                f'<rect x="{to_file * 45}" y="{to_rank * 45}" width="45" height="45" fill="#90EE90"/>'
            )
        
        # Ajouter un symbole texte pour le coup joué
        if self.index > 0:
            eval_info = self.evaluations[self.index - 1]
            to_square = eval_info["to_square"]
            file = chess.square_file(to_square)
            rank = 7 - chess.square_rank(to_square)
            x = file * 45 + 22.5
            y = rank * 45 + 15
            svg = svg.replace(
                '</svg>',
                f'<text x="{x}" y="{y}" font-size="12" font-family="Arial" text-anchor="middle">{eval_info["symbol"]}</text></svg>'
            )
            print(f"Symbole affiché pour coup {eval_info['move']}: {eval_info['symbol']} à x={x}, y={y}")
            move_text = f"Coup: {eval_info['move']} ({eval_info['quality'].capitalize()})"
        
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

if __name__ == "__main__":
    app = ChessViewer(boards, move_evaluations)
    app.mainloop()