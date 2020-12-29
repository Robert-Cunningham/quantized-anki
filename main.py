import sys
import os
from aqt import mw, QAction, QFileDialog
from pathlib import Path

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
                "id": n.id,
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


def importfn():
    with open("./user_files/quanta.yaml") as f:
        # with open("/home/robert/Documents/QKP/anki-exports/quanta.yaml") as f:
        yml = yaml.safe_load(f)
        saved_notes = yml["cards"]
        for saved_note in saved_notes:
            is_new = False
            try:
                note = mw.col.getNote(saved_note["id"])
            except:
                is_new = True

            if is_new:
                note = mw.col.newNote(True)

            note.fields = [
                saved_note[field_name]
                for field_name in model_to_fields[which_model(saved_note)]
            ]
            note.tags = saved_note["tags"]
            note.id = saved_note["id"]
            note.flush()
            if is_new:
                # showInfo(str(mw.col.decks.active()))
                mw.col.addNote(note)


user_files_path = Path(__file__).parent.joinpath("user_files")


def exportfn():
    # showInfo(str(user_files_path))
    cardCount = mw.col.cardCount()
    ids = mw.col.findCards("*")

    addClozeModel()
    addQAModel()

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
