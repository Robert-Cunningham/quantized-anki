import re
import sys
import os
from aqt import mw, QAction, QFileDialog, QKeySequence
from pathlib import Path
import anki.utils

sys.path.append(os.path.join(os.path.dirname(__file__), "dist"))

import yaml2 as yaml
from dulwich import porcelain
from aqt.qt import *
from aqt.utils import showInfo, chooseList, getText
from anki.hooks import addHook
from aqt import gui_hooks

from .models import *
from .exporter import *
from .importer import *
from .consts import *


def initialize(_):
    initialize_models()


def add_deck(disk_location, deck_name):
    did = mw.col.decks.id(deck_name)
    if user_decks_path.joinpath(deck_name).exists():
        showInfo("An anki deck with that name already exists.")
        return
    os.symlink(
        disk_location, user_decks_path.joinpath(deck_name),
    )


def import_remote():
    # https://raw.githubusercontent.com/Robert-Cunningham/quantized-decks/main/Test/quanta.yaml
    raw_path = getText(
        "What's the raw path to your quanta.yaml file? It should look like https://raw.githubusercontent.com/Robert-Cunningham/quantized-decks/main/Test/quanta.yaml."
    )[0]
    matched = re.match(
        r"https://raw\.githubusercontent\.com/([^/]*)/([^/]*)/([^/]*)/(?:(.*)/)?quanta\.yaml",
        raw_path.strip(),
    )
    github_user, github_repo, github_branch, github_path = matched.groups()

    try:
        git_decks_path.joinpath(github_user).joinpath(github_repo).mkdir(parents=True)
        repo = porcelain.clone(
            f"https://github.com/{github_user}/{github_repo}.git",
            str(git_decks_path.joinpath(github_user).joinpath(github_repo)),
        )
    except:
        # update_repos()
        pass

    with open(
        git_decks_path.joinpath(github_user)
        .joinpath(github_repo)
        .joinpath(github_path)
        .joinpath("quanta.yaml")
    ) as y:
        name = yaml.safe_load(y).get("meta", {}).get("name")

    add_deck(
        git_decks_path.joinpath(github_user)
        .joinpath(github_repo)
        .joinpath(github_path),
        name if name is not None else f"{github_user}/{github_repo}/{github_path}",
    )

    import_all()


def update_repos():
    [porcelain.pull(r) for r in repo.values()]


imp = QAction("Import remote quanta", mw)
imp.setShortcut(QKeySequence("Ctrl+Shift+R"))
imp.triggered.connect(import_remote)
mw.form.menuTools.addAction(imp)

init = QAction("Initialize QKP", mw)
init.triggered.connect(initialize)
mw.form.menuTools.addAction(init)

gui_hooks.collection_did_load.append(initialize)
