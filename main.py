import subprocess
import os

def main():
    username = input("Entrez le nom d'utilisateur Chess.com : ").strip()

    # Définir la variable d'environnement pour les scripts
    os.environ["CHESS_USERNAME"] = username

    print("\nTéléchargement de la dernière partie en cours...")
    subprocess.run(["python3", "retrieve_pgn.py"])

    print("\nAnalyse de la partie...")
    subprocess.run(["python3", "analyse.py"])

    print("\nAffichage des résultats...")
    subprocess.run(["python3", "afficher.py"])

if __name__ == "__main__":
    main()
