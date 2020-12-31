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

models = {
    "Quantized Knowledge QA": {
        "template": "Basic",
        "fields": [
            "front",
            "back",
            "answer_value",
            "answer_type",
            "explanation",
            "source",
        ],
    },
    "Quantized Knowledge Cloze": {
        "template": "Cloze",
        "fields": ["cloze", "explanation", "source"],
    },
    # "Quantized Knowledge Tag": [
    #     "name",
    #     "short name",
    #     "links",
    #     "explanation",
    #     "description",
    # ],
}

for m in models.keys():
    models[m]["anki_qfmt"] = "{{" + models[m]["fields"][0] + "}}"
    models[m]["anki_afmt"] = ["{{" + f + "}}<br><br>" for f in models[m]["fields"]]


class block(str):
    pass


def block_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


yaml.add_representer(block, block_presenter)


def yml_str(s):
    if "\n" in s:
        return block(s)
    else:
        return s


def toYaml(anki_note):
    for (model_name, model_fields) in model_to_fields.items():
        if anki_note.model()["name"] == model_name:
            out = {"id": anki_note.guid}

            if len(anki_note.tags) > 0:
                out["tags"] = anki_note.tags

            for (field_index, field_name) in enumerate(model_fields):
                if not anki_note.fields[field_index]:
                    continue

                if not "_" in field_name:
                    out[field_name] = yml_str(anki_note.fields[field_index])
                else:
                    items = field_name.split("_")
                    out.setdefault(items[0], {})
                    out[items[0]][items[1]] = anki_note.fields[field_index]

            for k in list(out.keys()):
                if out[k] == None:
                    del out[k]

            return out


basic_field = {
    "name": "Text",
    "ord": 0,
    "sticky": False,
    "rtl": False,
    "font": "Arial",
    "size": 20,
}


def addModel(model_name):
    model = models[model_name]
    if model_name not in mw.col.models.allNames():
        quanta_model = mw.col.models.copy(mw.col.models.byName(model["template"]))
        quanta_model["flds"] = []
        quanta_model["name"] = model_name
    else:
        quanta_model = mw.col.models.byName(model_name)

    quanta_model["flds"] = []
    for index, field in enumerate(model["fields"]):
        quanta_model["flds"].append({**basic_field, "name": field, "ord": index})

    quanta_model["tmpls"][0]["qfmt"] = model["anki_qfmt"]
    quanta_model["tmpls"][0]["afmt"] = model["anki_afmt"]

    mw.col.models.save(quanta_model)


def which_model(saved_note):
    if "cloze" in saved_note.keys():
        return "Quantized Knowledge Cloze"
    else:
        return "Quantized Knowledge QA"


def import_deck(name):
    did = mw.col.decks.id(name)
    with open(user_decks_path.joinpath(name).joinpath("quanta.yaml")) as f:
        yml = yaml.safe_load(f)
        if yml is None:
            return
        saved_notes = yml["cards"]
        for saved_note in saved_notes:
            save_note_to_collection(mw.col, did, saved_note)

            # is_new = False
            # try:
            #    note = mw.col.getNote(saved_note["id"])
            #    showInfo(f"Retrieved note {str(note)}")
            # except:
            #    is_new = True

            # if is_new:
            #    note = mw.col.newNote(True)

            # if is_new:
            #    # showInfo(str(mw.col.decks.active()))
            #    mw.col.addNote(note)

            # note.id = saved_note["id"]
            # note.flush()


# {
#    "__type__": "Note",
#    "data": "",
#    "fields": [
#        "（かをり）ん？ うん？",
#        "",
#        "<img src=\"Your_Lie_In_April_01_0.00.13.910.jpg\">",
#        "[sound:Your_Lie_In_April_01_0.00.13.138-0.00.14.681.mp3]",
#        "",
#        "",
#        "（かをり）ん？うん？"
#    ],
#    "flags": 0,
#    "guid": "eG2]e_:3Ll",
#    "note_model_uuid": "1a166fe2-1408-11eb-ae12-48e244f5452b",
#    "tags": [
#        "Your_Lie_In_April_01"
#    ]
# },


def deepget(nested_dict, key):
    keys = key.split("_")
    for k in keys:
        if isinstance(nested_dict, dict):
            nested_dict = nested_dict.get(k)
        else:
            return None

    return nested_dict


def save_note_to_collection(collection, deck_id, yml_note):
    note_model: NoteType = mw.col.models.byName(which_model(yml_note))
    guid = yml_note["id"]
    # note_model = deck.metadata.models[self.note_model_uuid]
    anki_object = get_note_by_guid(mw.col, guid)
    # if yml_note.get('answer', {}).get('type', "") == "@general/text/precise"

    new_note = anki_object is None
    if new_note:
        anki_object = AnkiNote(collection, note_model)
    else:
        pass
        # self.handle_model_update(collection, model_map_cache)
        # Should do this in case the card model has changed.

    # self.handle_import_config_changes(import_config, note_model)

    # self.anki_object.__dict__.update(self.anki_object_dict)
    anki_object.guid = bytes(str(yml_note["id"]), "utf8")
    anki_object.fields = [
        (
            deepget(yml_note, field_name)
            if deepget(yml_note, field_name) is not None
            else ""
        )
        for field_name in model_to_fields[which_model(yml_note)]
    ]
    anki_object.tags = yml_note.get("tags")
    anki_object.mid = note_model["id"]
    anki_object.mod = anki.utils.intTime()

    if new_note:
        collection.add_note(anki_object, deck_id)
    else:
        anki_object.flush()
        # self.move_cards_to_deck(deck_id)
        # for card in self.anki_object.cards():
        #    card.move_to_deck(deck_id, move_from_dynamic_decks=False)
        #    card.flush()


def get_note_by_guid(collection, uuid: str):
    query = "select id from notes where guid=?"
    note_id = collection.db.scalar(query, uuid)
    # showInfo(f"Tried to get a note by GUID {uuid}. Received {note_id}.")
    if not note_id:
        return None

    return AnkiNote(collection, id=note_id)


# def import_media(col, deck_folder):
#     media_directory = directory_path.joinpath("media")
#     if not media_directory.exists():
#         return
#     src_files = os.listdir(media_directory)
#     for filename in src_files:
#         full_filename = os.path.join(media_directory, filename)
#         if os.path.isfile(full_filename):
#             shutil.copy(full_filename, col.media.dir())


def importfn():
    initialize()
    files = os.listdir(user_decks_path)
    for f in files:
        # showInfo(f)
        if not os.path.isdir(user_decks_path.joinpath(f)):
            continue
        try:
            import_deck(f)
        except Exception as e:
            showInfo(f"{f} failed to import.")
            raise
    mw.deckBrowser.show()


def initialize():
    [addModel(k) for k in models.keys()]


def add_deck():
    pass


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


def exportfn():
    initialize()
    cardCount = mw.col.cardCount()
    ids = mw.col.findCards("*")

    # 'sortf': 0, 'did': 1609129183995, 'latexPre': '\\documentclass[12pt]{article}\n\\special{papersize=3in,5in}\n\\usepackage[utf8]{inputenc}\n\\usepackage{amssymb,amsmath}\n\\pagestyle{empty}\n\\setlength{\\parindent}{0in}\n\\begin{document}\n', 'latexPost': '\\end{document}', 'mod': 1609135853, 'usn': -1, 'vers': [], 'type': 0, 'css': '.card {\n font-family: arial;\n font-size: 20px;\n text-align: center;\n color: black;\n background-color: white;\n}\n', 'name': 'Basic',
    # 'flds': [{'name': 'Front', 'ord': 0, 'sticky': False, 'rtl': False, 'font': 'Arial', 'size': 20, 'media': []}, {'name': 'Back', 'ord': 1, 'sticky': False, 'rtl': False, 'font': 'Arial', 'size': 20, 'media': []}], 'tmpls': [{'name': 'Card 1', 'ord': 0, 'qfmt': '{{Front}}\n', 'afmt': '\n\n{{FrontSide}}\n\n \n\n{{Back}}', 'did': None, 'bqfmt': '', 'bafmt': ''}], 'tags': ['first-tag', 'second-tag'], 'id': '1609129140801', 'req': [[0, 'all', [0]]], 'crowdanki_uuid': '17158ed6-48c8-11eb-b662-48e244f5452b'}
    #        quanta_model['css'] = `.card {
    # font-size: 20px;
    # display: grid
    # background-color: white;
    # }`
    # mw.col.models.save(quanta_model)

    cards = [mw.col.getCard(id) for id in ids]
    nids = mw.col.findNotes(
        'note:"Quantized Knowledge QA" or note:"Quantized Knowledge Cloze"'
    )
    notes = [mw.col.getNote(nid) for nid in nids]

    #    data = [{
    #        "front": block(c.q()),
    #        "back": block(c.a()),
    #        "tags": c.note().tags,
    #        "id": c.id
    #        } for c in cards]
    #    data = [{
    #        "question": block(c.),
    #        "answer": block(c.a()),
    #        "tags": c.note().tags,
    #        "id": c.id
    #        } for c in cards]

    # with open("/home/robert/Documents/QKP/anki-exports/quanta.yaml", "w") as f:
    deck_names_and_ids = mw.col.decks.all_names_and_ids()
    # showInfo(str(deck_names_and_ids[0]))

    for deck_name_and_id in deck_names_and_ids:
        deck_id = deck_name_and_id.id
        deck_name = deck_name_and_id.name
        deck_notes = [n for n in notes if deck_id in [c.did for c in n.cards()]]
        data = [toYaml(n) for n in deck_notes]
        if len(data) > 0:
            write_deck(deck_name, data)


def write_deck(name, data):
    deck_path = user_decks_path.joinpath(name)
    deck_path.mkdir(exist_ok=True)
    with open(deck_path.joinpath("quanta.yaml"), "w") as f:
        yaml.dump({"cards": data}, f, default_flow_style=False, sort_keys=False)


export = QAction("Export quanta", mw)
export.setShortcut(QKeySequence("Ctrl+K"))
export.triggered.connect(exportfn)
mw.form.menuTools.addAction(export)

imp = QAction("Import local quanta", mw)
imp.setShortcut(QKeySequence("Ctrl+J"))
imp.triggered.connect(importfn)
mw.form.menuTools.addAction(imp)

imp = QAction("Import remote quanta", mw)
imp.setShortcut(QKeySequence("Ctrl+Shift+R"))
imp.triggered.connect(remote_importfn)
mw.form.menuTools.addAction(imp)

init = QAction("Initialize QKP", mw)
# imp.setShortcut(QKeySequence("Ctrl+Shift+R"))
imp.triggered.connect(initialize)
mw.form.menuTools.addAction(init)
