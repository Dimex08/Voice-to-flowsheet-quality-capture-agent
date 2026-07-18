"""Field registry for the legacy flowsheet — the target schema the narration agent fills in.

Every field is a dropdown (select), matching the legacy paper/EHR flowsheet
convention: a fixed set of clinically valid options, chosen either by a human
clicking the dropdown or by the extraction agent proposing a value.

Two scored neuro instruments live here:
- Glasgow Coma Scale (GCS): 3 items, total 3-15.
- NIH Stroke Scale (NIHSS): 15 items, total 0-42 (higher = worse).
"""


def _opts(*pairs):
    return [{"value": v, "label": l} for v, l in pairs]


FIELDS = [
    # ---------- Glasgow Coma Scale ----------
    {"id": "gcs_eye", "label": "GCS – Eye", "type": "select", "group": "Glasgow Coma Scale",
     "options": _opts(("4", "4 – Spontaneous"), ("3", "3 – To speech"),
                      ("2", "2 – To pain"), ("1", "1 – None"))},
    {"id": "gcs_verbal", "label": "GCS – Verbal", "type": "select", "group": "Glasgow Coma Scale",
     "options": _opts(("5", "5 – Oriented"), ("4", "4 – Confused"),
                      ("3", "3 – Inappropriate words"), ("2", "2 – Incomprehensible sounds"),
                      ("1", "1 – None"))},
    {"id": "gcs_motor", "label": "GCS – Motor", "type": "select", "group": "Glasgow Coma Scale",
     "options": _opts(("6", "6 – Obeys commands"), ("5", "5 – Localizes pain"),
                      ("4", "4 – Withdraws from pain"), ("3", "3 – Abnormal flexion"),
                      ("2", "2 – Abnormal extension"), ("1", "1 – None"))},

    # ---------- Pupils ----------
    {"id": "pupil_size_mm", "label": "Pupil Size", "type": "select", "group": "Pupils",
     "options": [{"value": str(n), "label": f"{n} mm"} for n in range(8, 1, -1)]},
    {"id": "pupil_reactivity", "label": "Pupil Reactivity", "type": "select", "group": "Pupils",
     "options": _opts(("Brisk bilaterally", "Brisk bilaterally"), ("Sluggish", "Sluggish"),
                      ("Fixed / nonreactive", "Fixed / nonreactive"), ("Unequal", "Unequal"))},

    # ---------- Neuro Exam ----------
    {"id": "facial_symmetry", "label": "Facial Symmetry", "type": "select", "group": "Neuro Exam",
     "options": _opts(("Symmetric", "Symmetric"), ("Droop – left", "Droop – left"),
                      ("Droop – right", "Droop – right"))},
    {"id": "speech", "label": "Speech", "type": "select", "group": "Neuro Exam",
     "options": _opts(("Clear", "Clear"), ("Slurred", "Slurred"),
                      ("Aphasic", "Aphasic"), ("Garbled", "Garbled"))},
    {"id": "strength", "label": "Motor Strength", "type": "select", "group": "Neuro Exam",
     "options": _opts(("Equal & strong x4", "Equal & strong x4"),
                      ("Unilateral weakness", "Unilateral weakness"),
                      ("Bilateral weakness", "Bilateral weakness"),
                      ("Unable to assess", "Unable to assess"))},
    {"id": "seizure_activity", "label": "Seizure Activity", "type": "select", "group": "Neuro Exam",
     "options": _opts(("None observed", "None observed"), ("Witnessed seizure", "Witnessed seizure"),
                      ("Post-ictal", "Post-ictal"))},

    # ---------- NIH Stroke Scale ----------
    {"id": "nihss_1a_loc", "label": "1a. LOC / Responsiveness", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Alert, keenly responsive"), ("1", "1 – Arousable to minor stimulation"),
                      ("2", "2 – Arousable only to repeated/painful stimulation"),
                      ("3", "3 – Coma / reflexive or unresponsive"))},
    {"id": "nihss_1b_questions", "label": "1b. LOC Questions (month, age)", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Both correct"), ("1", "1 – One correct"), ("2", "2 – Neither correct"))},
    {"id": "nihss_1c_commands", "label": "1c. LOC Commands (eyes, grip)", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Both tasks correct"), ("1", "1 – One task correct"), ("2", "2 – Neither correct"))},
    {"id": "nihss_2_gaze", "label": "2. Best Gaze", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Normal"), ("1", "1 – Partial gaze palsy"), ("2", "2 – Forced deviation"))},
    {"id": "nihss_3_visual", "label": "3. Visual Fields", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No visual loss"), ("1", "1 – Partial hemianopia"),
                      ("2", "2 – Complete hemianopia"), ("3", "3 – Bilateral hemianopia / blind"))},
    {"id": "nihss_4_facial", "label": "4. Facial Palsy", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Normal / symmetric"), ("1", "1 – Minor (flattened nasolabial fold)"),
                      ("2", "2 – Partial (lower face)"), ("3", "3 – Complete (upper & lower)"))},
    {"id": "nihss_5a_arm_l", "label": "5a. Motor Arm – Left", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No drift (holds 10s)"), ("1", "1 – Drift"),
                      ("2", "2 – Some effort against gravity"), ("3", "3 – No effort against gravity"),
                      ("4", "4 – No movement"))},
    {"id": "nihss_5b_arm_r", "label": "5b. Motor Arm – Right", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No drift (holds 10s)"), ("1", "1 – Drift"),
                      ("2", "2 – Some effort against gravity"), ("3", "3 – No effort against gravity"),
                      ("4", "4 – No movement"))},
    {"id": "nihss_6a_leg_l", "label": "6a. Motor Leg – Left", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No drift (holds 5s)"), ("1", "1 – Drift"),
                      ("2", "2 – Some effort against gravity"), ("3", "3 – No effort against gravity"),
                      ("4", "4 – No movement"))},
    {"id": "nihss_6b_leg_r", "label": "6b. Motor Leg – Right", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No drift (holds 5s)"), ("1", "1 – Drift"),
                      ("2", "2 – Some effort against gravity"), ("3", "3 – No effort against gravity"),
                      ("4", "4 – No movement"))},
    {"id": "nihss_7_ataxia", "label": "7. Limb Ataxia", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Absent"), ("1", "1 – One limb"), ("2", "2 – Two limbs"))},
    {"id": "nihss_8_sensory", "label": "8. Sensory", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Normal"), ("1", "1 – Mild–moderate loss"), ("2", "2 – Severe / total loss"))},
    {"id": "nihss_9_language", "label": "9. Best Language", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No aphasia"), ("1", "1 – Mild–moderate aphasia"),
                      ("2", "2 – Severe aphasia"), ("3", "3 – Mute / global aphasia"))},
    {"id": "nihss_10_dysarthria", "label": "10. Dysarthria", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – Normal"), ("1", "1 – Mild–moderate slurring"), ("2", "2 – Severe / unintelligible"))},
    {"id": "nihss_11_extinction", "label": "11. Extinction / Inattention", "type": "select", "group": "NIH Stroke Scale (NIHSS)",
     "options": _opts(("0", "0 – No abnormality"), ("1", "1 – Inattention to one modality"),
                      ("2", "2 – Profound hemi-inattention"))},
]

FIELDS_BY_ID = {f["id"]: f for f in FIELDS}

# Field-id lists for the scored instruments (used by the frontend totals + the
# consistency check).
GCS_FIELD_IDS = ["gcs_eye", "gcs_verbal", "gcs_motor"]
NIHSS_FIELD_IDS = [f["id"] for f in FIELDS if f["id"].startswith("nihss_")]


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
