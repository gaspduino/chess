import tkinter as tk
import chess
import chess.svg
from cairosvg import svg2png
from PIL import Image, ImageTk
import io

# === Lecture de la partie (PGN ou manuellement) ===
moves = [
    "e4", "e5", "Nf3", "Nc6", "Bc4", "Bc5", "c3", "Nf6", "d4", "exd4", "cxd4", "Bb4+"
]

board = chess.Board()
boards = [board.copy()]
for move in moves:
    board.push_san(move)
    boards.append(board.copy())

# === Interface ===
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
