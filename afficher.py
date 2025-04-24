import tkinter as tk
import chess
import chess.svg
import chess.pgn
from cairosvg import svg2png
from PIL import Image, ImageTk
import io
import os

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

# === Création des positions ===
board = game.board()
boards = [board.copy()]
for move in game.mainline_moves():
    board.push(move)
    boards.append(board.copy())

# === Interface graphique ===
class ChessViewer(tk.Tk):
    def __init__(self, positions):
        super().__init__()
        self.positions = positions
        self.index = 0

        self.title("Visualiseur d'échecs")
        self.geometry("500x500")

        self.canvas = tk.Label(self)
        self.canvas.pack()

        controls = tk.Frame(self)
        controls.pack()

        tk.Button(controls, text="⏮️", command=self.first).pack(side="left")
        tk.Button(controls, text="◀️", command=self.prev).pack(side="left")
        tk.Button(controls, text="▶️", command=self.next).pack(side="left")
        tk.Button(controls, text="⏭️", command=self.last).pack(side="left")

        self.show()

    def show(self):
        svg = chess.svg.board(self.positions[self.index], size=350)
        png_data = svg2png(bytestring=svg)
        image = Image.open(io.BytesIO(png_data))
        self.img = ImageTk.PhotoImage(image)
        self.canvas.config(image=self.img)

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
    app = ChessViewer(boards)
    app.mainloop()