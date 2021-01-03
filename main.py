import re
import sys
import os
from aqt import mw, QAction, QFileDialog, QKeySequence
from pathlib import Path
import anki.utils

sys.path.append(os.path.join(os.path.dirname(__file__), "dist"))

import yaml2 as yaml
from dulwich import porcelain
import glob
from aqt.qt import *
from aqt.utils import showInfo, chooseList, getText, getFile
from anki.hooks import addHook
from aqt import gui_hooks

from .models import *
from .exporter import *
from .importer import *
from .consts import *


def initialize(_):
    initialize_models()


def add_deck(disk_location):
    with open(Path(disk_location).joinpath("quanta.yaml")) as y:
        name = yaml.safe_load(y).get("meta", {}).get("name")

    deck_name = name if name is not None else str(disk_location).split("/")[-1]

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

    add_deck(
        git_decks_path.joinpath(github_user).joinpath(github_repo).joinpath(github_path)
    )

    import_all()


repo_list = glob.glob(str(git_decks_path) + "/*/*")


# def update_repos():
#     # export_all()
#     for r in repo_list:
#         showInfo(str(r))
#         porcelain.add(r, glob.glob(str(r) + "/**/*"))
#         porcelain.commit(r, "Update quanta")
#     # [porcelain.pull(r) for r in repo.values()]


def import_from_folder():
    # out = getFile(0, "Choose quanta.yaml", None, dir=True)
    folder = QFileDialog.getExistingDirectory(
        caption="Pick the folder which contains your quanta.yaml."
    )
    showInfo(str(folder))
    add_deck(folder)
    import_all()


imp = QAction("Import directly from GitHub", mw)
imp.setShortcut(QKeySequence("Ctrl+Shift+R"))
imp.triggered.connect(import_remote)
mw.form.menuTools.addAction(imp)

# send_changes = QAction("Send changes to GitHub", mw)
# # imp.setShortcut(QKeySequence("Ctrl+Shift+R"))
# send_changes.triggered.connect(update_repos)
# mw.form.menuTools.addAction(send_changes)

import_from_folder_action = QAction("Add local folder with quanta.yaml", mw)
import_from_folder_action.triggered.connect(import_from_folder)
mw.form.menuTools.addAction(import_from_folder_action)

gui_hooks.collection_did_load.append(initialize)
