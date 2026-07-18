"""FastAPI app: serves the legacy flowsheet + the fill-from-narration agent.

The legacy flowsheet (dropdown fields) is always manually editable in the UI.
POST /api/fill hands a pasted narration to the extraction agent, which fills the
dropdowns (or flags ambiguous fields), then scores the result on completeness /
correctness / currency.
"""

import json
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load backend/.env (ANTHROPIC_API_KEY) before importing agent, so the agent
# sees the key and runs live instead of in mock mode.
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI
from pydantic import BaseModel

import agent
import eval as evalmod
from schema import FIELDS

DATA_DIR = Path(__file__).parent / "data"
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

app = FastAPI(title="CodeScribe — Legacy Flowsheet Fill")


def _load(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text())


@app.get("/api/fields")
def get_fields():
    return FIELDS


@app.get("/api/scenarios")
def get_scenarios():
    # Only the input the UI needs — not the answer key (that stays server-side
    # until the eval runs, so the flowsheet isn't "graded" against a visible key).
    return [{"id": s["id"], "label": s["label"], "text": s["text"]}
            for s in _load("scenarios.json")]


class FillRequest(BaseModel):
    text: str
    scenario_id: Optional[str] = None


@app.post("/api/fill")
def fill(req: FillRequest):
    scenarios = {s["id"]: s for s in _load("scenarios.json")}
    ground_truth_all = _load("ground_truth.json")

    start = time.monotonic()
    result = agent.fill_flowsheet(req.text, req.scenario_id)
    fill_latency = time.monotonic() - start

    final_state = {u["field_id"]: u["value"] for u in result.get("updates", [])}
    flagged = {f["field_id"]: f for f in result.get("flags", [])}

    consistency = agent.check_consistency(final_state, result.get("stated_gcs_total"))

    response = {
        "mode": "mock" if agent.is_mock_mode() else "live",
        "updates": result.get("updates", []),
        "flags": result.get("flags", []),
        "consistency": consistency,
    }
    if result.get("mock_note"):
        response["mock_note"] = result["mock_note"]

    # Score only when we have an answer key for this scenario.
    ground_truth = ground_truth_all.get(req.scenario_id)
    if ground_truth:
        response["eval"] = evalmod.evaluate(
            final_state, fill_latency, ground_truth, set(flagged.keys())
        )
    else:
        response["eval"] = None
    return response


@app.get("/")
def index():
    from fastapi.responses import FileResponse
    return FileResponse(str(FRONTEND_DIR / "index.html"))


# Static assets (style.css, app.js) served alongside index.
from fastapi.staticfiles import StaticFiles  # noqa: E402
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
