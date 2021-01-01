import sys
import os
from aqt import mw, QAction, QFileDialog
from pathlib import Path
from anki.notes import Note as AnkiNote
import anki.utils
import pwd

sys.path.append(os.path.join(os.path.dirname(__file__), "dist"))

import yaml2 as yaml
from dulwich import porcelain
from aqt.qt import *
from aqt.utils import showInfo, chooseList

from models import *
from exporter import *
from importer import *


def initialize():
    initialize_models()


user_files_path = Path(__file__).parent.joinpath("user_files")
user_decks_path = user_files_path.joinpath("decks")
user_decks_path.mkdir(exist_ok=True)
git_decks_path = user_files_path.joinpath("repos")
git_decks_path.mkdir(exist_ok=True)
username = pwd.getpwuid(os.getuid()).pw_name


def remote_importfn():
    import_repo("Robert-Cunningham/quantized-decks")


repo = None
repo_name = None


def add_deck(deck_name):
    did = mw.col.decks.id(deck_name)
    if user_decks_path.joinpath(deck_name).exists():
        # showInfo("Anki deck already exists.")
        return
    os.symlink(
        git_decks_path.joinpath(repo_name).joinpath(deck_name),
        user_decks_path.joinpath(deck_name),
    )


def import_repo(_repo_name):
    # showInfo(username)
    global repo_name
    repo_name = _repo_name
    # askUserDialog(f"Which deck do you want to add from {_repo_name}?")
    git_decks = [str(x) for x in os.listdir(git_decks_path.joinpath(repo_name))]
    deck_name = git_decks[chooseList("Which deck do you want to import?", git_decks)]
    add_deck(deck_name)
    try:
        git_decks_path.joinpath(repo_name).mkdir(parents=True)
        repo = porcelain.clone(
            f"https://github.com/{repo_name}.git",
            str(git_decks_path.joinpath(repo_name)),
        )
    except:
        showInfo("Git deck already imported")
    # repos[repo_name] = repo
    importfn()


def update_repos():
    [porcelain.pull(r) for r in repo.values()]


imp = QAction("Import remote quanta", mw)
imp.setShortcut(QKeySequence("Ctrl+Shift+R"))
imp.triggered.connect(remote_importfn)
mw.form.menuTools.addAction(imp)

init = QAction("Initialize QKP", mw)
init.triggered.connect(initialize)
mw.form.menuTools.addAction(init)
