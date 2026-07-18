"""Field registry for the legacy flowsheet — the target schema the narration agent fills in.

Every field is a dropdown (select), matching the legacy paper/EHR flowsheet
convention: a fixed set of clinically valid options, chosen either by a human
clicking the dropdown or by the extraction agent proposing a value.
"""

FIELDS = [
    {"id": "gcs_eye", "label": "GCS – Eye", "type": "select", "group": "Glasgow Coma Scale",
     "options": [{"value": "4", "label": "4 – Spontaneous"},
                 {"value": "3", "label": "3 – To speech"},
                 {"value": "2", "label": "2 – To pain"},
                 {"value": "1", "label": "1 – None"}]},
    {"id": "gcs_verbal", "label": "GCS – Verbal", "type": "select", "group": "Glasgow Coma Scale",
     "options": [{"value": "5", "label": "5 – Oriented"},
                 {"value": "4", "label": "4 – Confused"},
                 {"value": "3", "label": "3 – Inappropriate words"},
                 {"value": "2", "label": "2 – Incomprehensible sounds"},
                 {"value": "1", "label": "1 – None"}]},
    {"id": "gcs_motor", "label": "GCS – Motor", "type": "select", "group": "Glasgow Coma Scale",
     "options": [{"value": "6", "label": "6 – Obeys commands"},
                 {"value": "5", "label": "5 – Localizes pain"},
                 {"value": "4", "label": "4 – Withdraws from pain"},
                 {"value": "3", "label": "3 – Abnormal flexion"},
                 {"value": "2", "label": "2 – Abnormal extension"},
                 {"value": "1", "label": "1 – None"}]},
    {"id": "pupil_size_mm", "label": "Pupil Size", "type": "select", "group": "Pupils",
     "options": [{"value": str(n), "label": f"{n} mm"} for n in range(8, 1, -1)]},
    {"id": "pupil_reactivity", "label": "Pupil Reactivity", "type": "select", "group": "Pupils",
     "options": [{"value": v, "label": v} for v in
                 ["Brisk bilaterally", "Sluggish", "Fixed / nonreactive", "Unequal"]]},
    {"id": "facial_symmetry", "label": "Facial Symmetry", "type": "select", "group": "Neuro Exam",
     "options": [{"value": v, "label": v} for v in
                 ["Symmetric", "Droop – left", "Droop – right"]]},
    {"id": "speech", "label": "Speech", "type": "select", "group": "Neuro Exam",
     "options": [{"value": v, "label": v} for v in
                 ["Clear", "Slurred", "Aphasic", "Garbled"]]},
    {"id": "strength", "label": "Motor Strength", "type": "select", "group": "Neuro Exam",
     "options": [{"value": v, "label": v} for v in
                 ["Equal & strong x4", "Unilateral weakness", "Bilateral weakness", "Unable to assess"]]},
    {"id": "seizure_activity", "label": "Seizure Activity", "type": "select", "group": "Neuro Exam",
     "options": [{"value": v, "label": v} for v in
                 ["None observed", "Witnessed seizure", "Post-ictal"]]},
]

FIELDS_BY_ID = {f["id"]: f for f in FIELDS}


def valid_value(field_id: str, value: str) -> bool:
    field = FIELDS_BY_ID.get(field_id)
    if field is None:
        return False
    if field["type"] == "select":
        return value in {o["value"] for o in field["options"]}
    if field["type"] == "number":
        try:
            float(value)
            return True
        except (TypeError, ValueError):
            return False
    return False
