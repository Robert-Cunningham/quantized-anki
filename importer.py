from aqt import mw, QAction, QFileDialog, QKeySequence
import os
from aqt.utils import showInfo
import yaml2 as yaml
from anki.notes import Note as AnkiNote
import anki.utils
from .models import *
from .consts import *


def import_deck(quanta_path):
    with open(quanta_path) as f:
        yml = yaml.safe_load(f)
        if yml is None:
            return

        did = mw.col.decks.id(yml.get("meta", {}).get("name", "Untitled Deck"))
        saved_notes = yml["cards"]
        for saved_note in saved_notes:
            save_note_to_collection(mw.col, did, saved_note)


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
        (
            deepget(yml_note, field_name)
            if deepget(yml_note, field_name) is not None
            else ""
        )
        for field_name in models[which_model(yml_note)]["fields"]
    ]
    # showInfo(str(anki_object.fields))
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


def import_all():
    files = os.listdir(user_decks_path)
    for f in files:
        # showInfo(f)
        if not os.path.isdir(user_decks_path.joinpath(f)):
            continue
        try:
            import_deck(user_decks_path.joinpath(f).joinpath("quanta.yaml"))
        except Exception as e:
            showInfo(f"{f} failed to import.")
            raise
    mw.deckBrowser.show()


import_all_action = QAction("Import local quanta", mw)
import_all_action.setShortcut(QKeySequence("Ctrl+I"))
import_all_action.triggered.connect(import_all)
mw.form.menuTools.addAction(import_all_action)
