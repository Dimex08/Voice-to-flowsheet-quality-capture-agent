"""Three-axis documentation-quality eval: completeness, correctness, currency.

Framework mirrors the EHR data-quality literature (completeness / correctness /
currency; see PMID 37740937).

completeness — of all fields the flowsheet defines, how many did the agent chart.
    A field the agent deliberately flagged for human review counts as incomplete,
    not wrong — that is the completeness↔correctness tradeoff the flag creates.
correctness  — of the fields the agent DID chart, how many match the ground-truth
    value a human reviewer established.
currency     — real wall-clock seconds from paste to a filled flowsheet, mapped to
    a 0-100 score via a decay curve, contrasted with legacy retrospective charting
    (a nurse batch-charting minutes-to-hours later). The legacy figure is a fixed
    illustrative comparison point, not a cited statistic.
"""

from schema import FIELDS

LEGACY_CHARTING_LAG_SECONDS = 45 * 60  # illustrative: end-of-round paper charting, not a cited figure
CURRENCY_HALF_LIFE_SECONDS = 30       # fill latency at which the currency score hits 50


def currency_score(latency_seconds: float) -> float:
    if latency_seconds is None or latency_seconds <= 0:
        return 100.0
    score = 100.0 * (0.5 ** (latency_seconds / CURRENCY_HALF_LIFE_SECONDS))
    return round(max(score, 0.0), 1)


def evaluate(final_state: dict, fill_latency_seconds: float, ground_truth: dict,
             flagged_field_ids: set) -> dict:
    """
    final_state:        {field_id: value}              — what ended up charted
    fill_latency_seconds: seconds from paste to filled flowsheet
    ground_truth:       {field_id: {value, note}}      — answer key
    flagged_field_ids:  fields the agent left for human confirmation

    Scoring is scoped to the fields this assessment is supposed to capture —
    i.e. the ground-truth field set — not the entire flowsheet. A stroke NIHSS
    exam doesn't assess GCS/pupils, so those fields aren't "incomplete"; they're
    out of scope for this note.
    """
    in_scope = list(ground_truth.keys())
    charted_ids = [fid for fid in in_scope if fid in final_state]

    completeness = len(charted_ids) / len(in_scope) if in_scope else 0.0

    correct = [fid for fid in charted_ids
               if final_state[fid] == ground_truth.get(fid, {}).get("value")]
    correctness = (len(correct) / len(charted_ids)) if charted_ids else 0.0

    per_field = []
    for fid in in_scope:
        gt = ground_truth.get(fid, {})
        row = {"field_id": fid, "ground_truth": gt.get("value")}
        if fid in final_state:
            row["status"] = "correct" if fid in correct else "incorrect"
            row["charted_value"] = final_state[fid]
        elif fid in flagged_field_ids:
            row["status"] = "flagged"
            row["charted_value"] = None
        else:
            row["status"] = "missing"
            row["charted_value"] = None
        per_field.append(row)

    # Fields the agent charted that are outside this assessment's scope — not
    # graded, but surfaced honestly so over-charting is visible.
    flagged_in_scope = [fid for fid in in_scope if fid in flagged_field_ids]
    extra = [fid for fid in final_state if fid not in ground_truth]

    return {
        "completeness": round(completeness * 100, 1),
        "correctness": round(correctness * 100, 1),
        "currency": currency_score(fill_latency_seconds),
        "fill_latency_seconds": round(fill_latency_seconds, 2) if fill_latency_seconds else None,
        "legacy_charting_lag_seconds": LEGACY_CHARTING_LAG_SECONDS,
        "fields_total": len(in_scope),
        "fields_charted": len(charted_ids),
        "fields_correct": len(correct),
        "fields_flagged": len(flagged_in_scope),
        "fields_extra": len(extra),
        "per_field": per_field,
    }
