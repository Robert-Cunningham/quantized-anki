from aqt import mw
from aqt.utils import showInfo


add_to_all_sides = """ """

models = {
    "Quantized Knowledge QA": {
        "template": "Basic",
        "fields": ["front", "back", "answer_value", "explanation", "source",],
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
    models[m]["anki_qfmt"] = "{{" + models[m]["fields"][0] + "}}" + add_to_all_sides
    models[m]["anki_afmt"] = (
        "".join(["{{" + f + "}}<br><br>" for f in models[m]["fields"]])
        + add_to_all_sides
    )


def initialize_models():
    [addModel(k) for k in models.keys()]


basic_field = {
    "name": "Text",
    "ord": 0,
    "sticky": False,
    "rtl": False,
    "font": "Arial",
    "size": 20,
}


def addModel(model_name):
    mw.backup()
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
