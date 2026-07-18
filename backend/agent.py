"""Extraction agent: turns a pasted narration into legacy-flowsheet field values.

The nurse's spoken (then transcribed) narration is handed to the agent as one
block of text. The agent maps it onto the discrete dropdown fields of the legacy
flowsheet, and — where the narration is genuinely ambiguous — flags the field
with a drafted clarifying question instead of guessing. A separate deterministic
consistency check (check_consistency) re-verifies the agent's own output.
"""

import os
import random
import time

import anthropic

from schema import FIELDS, valid_value

# Extraction is short, structured tool-call work — Sonnet 5 handles it well at a
# lower price than Opus. Override with CODESCRIBE_MODEL (e.g. claude-haiku-4-5 to
# go cheaper still, or claude-opus-4-8 for maximum capability).
MODEL = os.environ.get("CODESCRIBE_MODEL", "claude-sonnet-5")

TOOL = {
    "name": "fill_flowsheet",
    "description": (
        "Map the nurse's narration onto the legacy flowsheet's dropdown fields, "
        "or flag a field for human confirmation instead of guessing when the "
        "narration is genuinely ambiguous or internally inconsistent."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "updates": {
                "type": "array",
                "description": "Fields you are confident enough to chart.",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_id": {"type": "string"},
                        "value": {"type": "string", "description": "Must be one of the field's allowed option values."},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "quote": {"type": "string", "description": "The exact words from the narration this was extracted from."},
                    },
                    "required": ["field_id", "value", "confidence", "quote"],
                },
            },
            "flags": {
                "type": "array",
                "description": "Fields deliberately left unfilled because the narration doesn't support a single confident value.",
                "items": {
                    "type": "object",
                    "properties": {
                        "field_id": {"type": "string"},
                        "reason": {"type": "string"},
                        "quote": {"type": "string"},
                        "clarifying_question": {
                            "type": "string",
                            "description": "The exact question a scribe should ask the care team to resolve this.",
                        },
                    },
                    "required": ["field_id", "reason", "quote", "clarifying_question"],
                },
            },
            "stated_gcs_total": {
                "type": ["integer", "null"],
                "description": "The overall GCS the nurse stated aloud (e.g. 'Glasgow fifteen' -> 15), or null if none was stated. Used only for the consistency cross-check, not charted.",
            },
        },
        "required": ["updates", "flags"],
    },
}


def _field_registry_prompt() -> str:
    lines = []
    for f in FIELDS:
        opts = ", ".join(f'"{o["value"]}"' for o in f["options"])
        lines.append(f'- {f["id"]} ({f["label"]}): one of [{opts}]')
    return "\n".join(lines)


SYSTEM_PROMPT = f"""You are a clinical documentation agent. A nurse has narrated a \
bedside neuro assessment out loud; you receive the transcribed narration and must \
map it onto a legacy nursing flowsheet made of fixed dropdown fields.

Flowsheet fields and their allowed values:
{_field_registry_prompt()}

Rules:
1. Chart a field only when the narration clearly supports exactly one of its \
allowed values. Use the option value verbatim (e.g. gcs_motor must be one of \
"6","5","4","3","2","1").
2. If the narration gives two candidate values with no clear resolution, or is \
internally inconsistent, do NOT guess. Put the field in `flags` with a short \
reason and a `clarifying_question` a scribe could ask out loud.
3. For GCS motor, when sides differ, the exam is scored on the best response — but \
if the narration is ambiguous about which response was elicited, flag it.
4. Never fabricate a value the narration doesn't support.
5. If the nurse states an overall Glasgow total, return it as `stated_gcs_total` \
so it can be cross-checked against the E+V+M you charted."""


def _client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Export it before running the server."
        )
    return anthropic.Anthropic(api_key=api_key)


def is_mock_mode() -> bool:
    if os.environ.get("CODESCRIBE_FORCE_LIVE"):
        return False
    return not bool(os.environ.get("ANTHROPIC_API_KEY"))


# Scripted stand-ins for the Claude tool-use call, keyed by scenario id
# (backend/data/scenarios.json). Same shape the real call returns, so
# main.py / eval.py don't know or care which path ran. Used when no
# ANTHROPIC_API_KEY is set, so the pipeline is demoable before the key is
# wired in. The ambiguity in `arousal_ambiguous` is flagged here exactly as
# the system prompt instructs the live model to flag it — a fixture of the
# demo scenario, not a shortcut around the agent's judgment.
_MOCK_BY_SCENARIO = {
    "fall_clean": {
        "updates": [
            {"field_id": "gcs_eye", "value": "4", "confidence": 0.98, "quote": "Eyes are open spontaneously"},
            {"field_id": "gcs_verbal", "value": "5", "confidence": 0.98, "quote": "Fully oriented"},
            {"field_id": "gcs_motor", "value": "6", "confidence": 0.98, "quote": "Follows commands"},
            {"field_id": "pupil_size_mm", "value": "4", "confidence": 0.96, "quote": "4 millimeters"},
            {"field_id": "pupil_reactivity", "value": "Brisk bilaterally", "confidence": 0.95, "quote": "brisk both sides"},
            {"field_id": "facial_symmetry", "value": "Symmetric", "confidence": 0.97, "quote": "Face symmetric"},
            {"field_id": "speech", "value": "Clear", "confidence": 0.97, "quote": "Speech clear"},
            {"field_id": "strength", "value": "Equal & strong x4", "confidence": 0.96, "quote": "Strength equal and strong, all four extremities"},
            {"field_id": "seizure_activity", "value": "None observed", "confidence": 0.97, "quote": "No seizure activity"},
        ],
        "flags": [],
        "stated_gcs_total": 15,
    },
    "arousal_ambiguous": {
        "updates": [
            {"field_id": "gcs_verbal", "value": "4", "confidence": 0.82, "quote": "speech was a little thick but she told me her name. Didn't quite track the date"},
            {"field_id": "gcs_motor", "value": "4", "confidence": 0.78, "quote": "the left just kind of pulled back"},
            {"field_id": "pupil_size_mm", "value": "3", "confidence": 0.95, "quote": "Pupils three millimeters"},
            {"field_id": "pupil_reactivity", "value": "Brisk bilaterally", "confidence": 0.85, "quote": "equal, react"},
            {"field_id": "facial_symmetry", "value": "Symmetric", "confidence": 0.9, "quote": "No facial droop that I could see"},
            {"field_id": "speech", "value": "Slurred", "confidence": 0.8, "quote": "speech was a little thick"},
            {"field_id": "strength", "value": "Unilateral weakness", "confidence": 0.8, "quote": "Moved her right arm... the left just kind of pulled back"},
            {"field_id": "seizure_activity", "value": "None observed", "confidence": 0.95, "quote": "No seizures"},
        ],
        "flags": [
            {"field_id": "gcs_eye",
             "reason": "Eye-opening could be 'to speech' (3) or 'spontaneous' (4) — nurse notes she may have been waking on her own.",
             "quote": "I said her name and she opened them, though honestly she may have been starting to wake up on her own",
             "clarifying_question": "GCS eye-opening — did she open her eyes because you said her name (score 3), or was she already opening them spontaneously (score 4)?"},
        ],
        "stated_gcs_total": None,
    },
    "stroke_nihss": {
        "updates": [
            {"field_id": "nihss_1a_loc", "value": "0", "confidence": 0.95, "quote": "She's alert and answering"},
            {"field_id": "nihss_1b_questions", "value": "0", "confidence": 0.95, "quote": "She told me the month and her age, both correct"},
            {"field_id": "nihss_1c_commands", "value": "0", "confidence": 0.94, "quote": "opens and closes her eyes on command and grips and releases my hand on command"},
            {"field_id": "nihss_2_gaze", "value": "1", "confidence": 0.9, "quote": "partial gaze palsy"},
            {"field_id": "nihss_3_visual", "value": "2", "confidence": 0.9, "quote": "complete left homonymous hemianopia"},
            {"field_id": "nihss_4_facial", "value": "2", "confidence": 0.88, "quote": "left lower facial droop, partial paralysis"},
            {"field_id": "nihss_5a_arm_l", "value": "1", "confidence": 0.87, "quote": "Her left arm drifts down before ten seconds"},
            {"field_id": "nihss_5b_arm_r", "value": "0", "confidence": 0.93, "quote": "The right arm holds with no drift"},
            {"field_id": "nihss_6a_leg_l", "value": "2", "confidence": 0.85, "quote": "left leg has some effort against gravity but drops to the bed"},
            {"field_id": "nihss_6b_leg_r", "value": "0", "confidence": 0.92, "quote": "The right leg holds"},
            {"field_id": "nihss_7_ataxia", "value": "0", "confidence": 0.92, "quote": "No limb ataxia"},
            {"field_id": "nihss_8_sensory", "value": "1", "confidence": 0.86, "quote": "Decreased sensation on the left to pinprick, mild to moderate"},
            {"field_id": "nihss_9_language", "value": "1", "confidence": 0.85, "quote": "mild expressive aphasia"},
            {"field_id": "nihss_10_dysarthria", "value": "1", "confidence": 0.85, "quote": "Her speech is mildly slurred, dysarthria is present but intelligible"},
            {"field_id": "nihss_11_extinction", "value": "1", "confidence": 0.86, "quote": "clear left-sided inattention"},
        ],
        "flags": [],
        "stated_gcs_total": None,
    },
    # Comprehensive case — exercises every field group, varied confidence, a
    # stated GCS total (for the consistency cross-check), and one genuinely
    # ambiguous field (limb ataxia untestable in a weak limb) that is flagged
    # rather than guessed.
    "comprehensive_stroke": {
        "updates": [
            {"field_id": "gcs_eye", "value": "4", "confidence": 0.97, "quote": "Her eyes are open spontaneously"},
            {"field_id": "gcs_verbal", "value": "4", "confidence": 0.83, "quote": "She's confused — she knew her age but couldn't tell me the month, and her words are jumbled"},
            {"field_id": "gcs_motor", "value": "6", "confidence": 0.95, "quote": "She does follow commands, squeezed my hand and stuck out her tongue on request"},
            {"field_id": "pupil_size_mm", "value": "3", "confidence": 0.96, "quote": "Her pupils are three millimeters"},
            {"field_id": "pupil_reactivity", "value": "Brisk bilaterally", "confidence": 0.93, "quote": "equal and briskly reactive"},
            {"field_id": "facial_symmetry", "value": "Droop – left", "confidence": 0.94, "quote": "an obvious left facial droop"},
            {"field_id": "speech", "value": "Aphasic", "confidence": 0.88, "quote": "clear expressive aphasia"},
            {"field_id": "strength", "value": "Unilateral weakness", "confidence": 0.92, "quote": "Left-sided weakness throughout"},
            {"field_id": "seizure_activity", "value": "None observed", "confidence": 0.96, "quote": "No seizure activity"},
            {"field_id": "nihss_1a_loc", "value": "0", "confidence": 0.94, "quote": "Level of consciousness, she's alert"},
            {"field_id": "nihss_1b_questions", "value": "1", "confidence": 0.86, "quote": "she got her age right but not the month, so one correct"},
            {"field_id": "nihss_1c_commands", "value": "0", "confidence": 0.93, "quote": "Commands, she did both — eyes and grip"},
            {"field_id": "nihss_2_gaze", "value": "1", "confidence": 0.88, "quote": "Her gaze shows a partial palsy"},
            {"field_id": "nihss_3_visual", "value": "2", "confidence": 0.9, "quote": "complete left homonymous hemianopia"},
            {"field_id": "nihss_4_facial", "value": "2", "confidence": 0.87, "quote": "Facial, partial lower-face droop"},
            {"field_id": "nihss_5a_arm_l", "value": "2", "confidence": 0.82, "quote": "Left arm, she gets it up but it drifts down with some effort against gravity"},
            {"field_id": "nihss_5b_arm_r", "value": "0", "confidence": 0.93, "quote": "Right arm holds fine"},
            {"field_id": "nihss_6a_leg_l", "value": "1", "confidence": 0.83, "quote": "Left leg drifts but keeps some effort"},
            {"field_id": "nihss_6b_leg_r", "value": "0", "confidence": 0.93, "quote": "Right leg is normal"},
            {"field_id": "nihss_8_sensory", "value": "1", "confidence": 0.84, "quote": "Sensation is reduced on the left, mild to moderate"},
            {"field_id": "nihss_9_language", "value": "1", "confidence": 0.84, "quote": "Language, mild to moderate aphasia"},
            {"field_id": "nihss_10_dysarthria", "value": "1", "confidence": 0.84, "quote": "Her speech is mildly slurred, dysarthria present"},
            {"field_id": "nihss_11_extinction", "value": "1", "confidence": 0.86, "quote": "she's clearly neglecting her left side, inattention"},
        ],
        "flags": [
            {"field_id": "nihss_7_ataxia",
             "reason": "Nurse states limb ataxia could not be reliably assessed because of the left-sided weakness, and is unsure whether to score it absent (0) or untestable.",
             "quote": "I honestly couldn't reliably test for limb ataxia given how weak that side is — not sure whether to call it absent or untestable",
             "clarifying_question": "NIHSS limb ataxia — since the left side is too weak to test reliably, should this be scored 0 (absent) per the untestable-limb convention, or documented as not assessed?"},
        ],
        "stated_gcs_total": 14,
    },
}


def _propose_mock(scenario_id: str) -> dict:
    time.sleep(random.uniform(0.6, 1.2))  # order-of-magnitude realistic call latency
    result = _MOCK_BY_SCENARIO.get(scenario_id)
    if result is None:
        # Unknown / edited text: mock mode can't script it. Be honest rather than fake a fill.
        return {"updates": [], "flags": [], "stated_gcs_total": None,
                "mock_note": "Mock mode only scripts the built-in sample narratives. "
                             "Set ANTHROPIC_API_KEY to run the real agent on arbitrary text."}
    return {
        "updates": list(result["updates"]),
        "flags": list(result["flags"]),
        "stated_gcs_total": result.get("stated_gcs_total"),
    }


def fill_flowsheet(narration: str, scenario_id: str = None) -> dict:
    """Map a narration onto flowsheet fields. Returns {updates, flags, stated_gcs_total}.

    Live Claude call when ANTHROPIC_API_KEY is set; otherwise scripted per-scenario
    mock (see is_mock_mode / _MOCK_BY_SCENARIO)."""
    if is_mock_mode():
        return _propose_mock(scenario_id)
    return _fill_flowsheet_live(narration)


def _fill_flowsheet_live(narration: str) -> dict:
    client = _client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": "fill_flowsheet"},
        messages=[{"role": "user", "content": f"Narration:\n{narration}"}],
    )
    for block in message.content:
        if block.type == "tool_use" and block.name == "fill_flowsheet":
            result = dict(block.input)
            result["updates"] = [
                u for u in result.get("updates", []) if valid_value(u["field_id"], u["value"])
            ]
            result.setdefault("flags", [])
            result.setdefault("stated_gcs_total", None)
            return result
    return {"updates": [], "flags": [], "stated_gcs_total": None}


def check_consistency(state: dict, stated_gcs_total=None) -> list:
    """Deterministic cross-check of the agent's own output — the adversarial layer,
    independent of the LLM call. Returns a list of {level, message} where level is
    'ok' or 'warning', so the panel can show green confirmations as well as flags.

    Checks:
    - GCS total is recomputed from the charted E/V/M sub-scores and range-checked (3-15).
    - If the nurse stated an overall Glasgow total, it is compared against that sum —
      a mismatch implies a mis-charted sub-score or a mis-heard total.
    """
    issues = []
    e, v, m = state.get("gcs_eye"), state.get("gcs_verbal"), state.get("gcs_motor")
    if e and v and m:
        total = int(e) + int(v) + int(m)
        if not (3 <= total <= 15):
            issues.append({"level": "warning",
                           "message": f"GCS sub-scores sum to {total}, outside the valid range 3–15."})
        elif stated_gcs_total is not None and total != stated_gcs_total:
            issues.append({"level": "warning",
                           "message": f"Charted GCS {e}+{v}+{m}={total} does not match the stated "
                                      f"total of {stated_gcs_total} — verify the sub-scores."})
        elif stated_gcs_total is not None:
            issues.append({"level": "ok",
                           "message": f"GCS {e}+{v}+{m}={total} matches the stated total of "
                                      f"{stated_gcs_total} — internally consistent."})
        else:
            issues.append({"level": "ok",
                           "message": f"GCS sub-scores sum to {total}, within the valid range 3–15."})
    return issues
