from aqt import mw, QAction, QKeySequence
import yaml2 as yaml
from .models import models
from .consts import *
from .utils import *


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


def note_to_yaml(anki_note):
    for (model_name, model_data) in models.items():
        model_fields = model_data["fields"]
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


def export_all():
    nids = mw.col.findNotes(
        'note:"Quantized Knowledge QA" or note:"Quantized Knowledge Cloze"'
    )
    notes = [mw.col.getNote(nid) for nid in nids]
    deck_names_and_ids = mw.col.decks.all_names_and_ids()

    for deck_name_and_id in deck_names_and_ids:
        deck_id = deck_name_and_id.id
        deck_name = deck_name_and_id.name
        deck_notes = [n for n in notes if deck_id in [c.did for c in n.cards()]]
        data = [note_to_yaml(n) for n in deck_notes]
        if len(data) > 0:
            write_deck_to_disk(deck_name, {"meta": {"name": deck_name}, "cards": data})


def write_deck_to_disk(name, quanta):
    deck_path = user_decks_path.joinpath(name)
    deck_path.mkdir(exist_ok=True)
    try:
        with open(deck_path.joinpath("quanta.yaml")) as f:
            pre_existing = yaml.safe_load(f)["cards"]
        pre_existing_by_id = {p["id"]: p for p in pre_existing}

    except Exception as e:
        pre_existing_by_id = {}

    for (i, q) in enumerate(quanta["cards"]):
        prex_card = pre_existing_by_id.get(q["id"], {})
        update(prex_card, q)
        quanta["cards"][i] = prex_card

    with open(deck_path.joinpath("quanta.yaml"), "w") as f:
        yaml.dump(quanta, f, default_flow_style=False, sort_keys=False)


export_all_action = QAction("Export to quanta.yamls", mw)
export_all_action.setShortcut(QKeySequence("Ctrl+Shift+E"))
export_all_action.triggered.connect(export_all)
mw.form.menuTools.addAction(export_all_action)
