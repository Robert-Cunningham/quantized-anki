from pathlib import Path
import os

user_files_path = Path(__file__).parent.joinpath("user_files")
user_decks_path = user_files_path.joinpath("decks")
user_decks_path.mkdir(exist_ok=True)
git_decks_path = user_files_path.joinpath("repos")
git_decks_path.mkdir(exist_ok=True)
