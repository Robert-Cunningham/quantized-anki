import sys
import os
from aqt import mw, QAction, QFileDialog
from pathlib import Path
from anki.notes import Note as AnkiNote
import anki.utils

sys.path.append(os.path.join(os.path.dirname(__file__), "dist"))

import yaml2 as yaml
from aqt.qt import *
from aqt.utils import showInfo

model_to_fields = {
    "Quantized Knowledge QA": ["question", "answer", "explanation"],
    "Quantized Knowledge Cloze": ["cloze", "explanation"],
    # "Quantized Knowledge Tag": [
    #     "name",
    #     "short name",
    #     "links",
    #     "explanation",
    #     "description",
    # ],
}

QKP_ID_FIELD = "qkp_id"


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


def toYaml(n):
    for (model_name, model_fields) in model_to_fields.items():
        if n.model()["name"] == model_name:
            return {
                **{
                    field_name: yml_str(n.fields[field_index])
                    for (field_index, field_name) in enumerate(model_fields)
                },
                # "question": yml_str(n.fields[0]),
                # "answer": yml_str(n.fields[1]),
                # "explanation": yml_str(n.fields[2]),
                "tags": n.tags,
                "id": n.guid,
            }


def addClozeModel():
    model_name = "Quantized Knowledge Cloze"
    if model_name not in mw.col.models.allNames():
        quanta_model = mw.col.models.copy(mw.col.models.byName("Cloze"))
        info_field = quanta_model["flds"].pop(1)
        quanta_model["flds"].append({**info_field, "name": "Explanation", "ord": 1})
        quanta_model["name"] = model_name
        mw.col.models.save(quanta_model)


def addQAModel():
    model_name = "Quantized Knowledge QA"
    if model_name not in mw.col.models.allNames():
        quanta_model = mw.col.models.copy(mw.col.models.byName("Basic"))
        showInfo(str(quanta_model))
        quanta_model["flds"].append(
            {**quanta_model["flds"][0], "name": "Explanation", "ord": 2}
        )
        quanta_model["name"] = model_name
        mw.col.models.save(quanta_model)


def which_model(saved_note):
    if "cloze" in saved_note.keys():
        return "Quantized Knowledge Cloze"
    else:
        return "Quantized Knowledge QA"


def import_deck(name):
    showInfo(str(user_files_path.joinpath(name).joinpath("quanta.yaml")))
    with open(user_files_path.joinpath(name).joinpath("quanta.yaml")) as f:
        # with open("/home/robert/Documents/QKP/anki-exports/quanta.yaml") as f:
        yml = yaml.safe_load(f)
        if yml is None:
            return
        saved_notes = yml["cards"]
        for saved_note in saved_notes:
            save_note_to_collection(mw.col, 0, saved_note)

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


def save_note_to_collection(collection, deck_id, yml_note):
    note_model: NoteType = mw.col.models.byName(which_model(yml_note))
    guid = yml_note["id"]
    # note_model = deck.metadata.models[self.note_model_uuid]
    anki_object = get_note_by_guid(mw.col, guid)

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
        yml_note[field_name] for field_name in model_to_fields[which_model(yml_note)]
    ]
    anki_object.tags = yml_note["tags"]
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
    showInfo(f"Tried to get a note by GUID {uuid}. Received {note_id}.")
    if not note_id:
        return None

    return AnkiNote(collection, id=note_id)


def importfn():
    initialize()
    files = os.listdir(user_files_path)
    for f in files:
        # showInfo(f)
        if not os.path.isdir(user_files_path.joinpath(f)):
            continue
        try:
            import_deck(f)
        except Exception as e:
            showInfo(f"{f} failed to import.")
            raise


def initialize():
    addClozeModel()
    addQAModel()


def add_deck():
    pass


user_files_path = Path(__file__).parent.joinpath("user_files")


def exportfn():
    initialize()
    # showInfo(str(user_files_path))
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
    showInfo(str(deck_names_and_ids[0]))

    for deck_name_and_id in deck_names_and_ids:
        deck_id = deck_name_and_id.id
        deck_name = deck_name_and_id.name
        deck_notes = [n for n in notes if deck_id in [c.did for c in n.cards()]]
        data = [toYaml(n) for n in deck_notes]
        if len(data) > 0:
            write_deck(deck_name, data)


def write_deck(name, data):
    user_files_path.joinpath(name).mkdir(exist_ok=True)
    with open(user_files_path.joinpath(name).joinpath("quanta.yaml"), "w") as f:
        yaml.dump({"cards": data}, f, default_flow_style=False, sort_keys=False)


export = QAction("Export quanta", mw)
export.setShortcut(QKeySequence("Ctrl+K"))
export.triggered.connect(exportfn)
mw.form.menuTools.addAction(export)

imp = QAction("Import quanta", mw)
imp.setShortcut(QKeySequence("Ctrl+J"))
imp.triggered.connect(importfn)
mw.form.menuTools.addAction(imp)
