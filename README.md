# CodeScribe — narration → legacy neuro flowsheet, with live eval scoring

A legacy nursing flowsheet: Glasgow Coma Scale (Eye/Verbal/Motor), pupils, and
neuro-exam fields, each a dropdown you can set by hand — the "old system." A
separate agent (Claude) reads a nurse's pasted narration and fills those dropdowns
for you, then scores the result on three axes of documentation quality:
**completeness**, **correctness**, and **currency** (framework mirrors PMID 37740937).

The point of contrast: the flowsheet is fully usable by hand (that's the legacy
baseline), and the agent is a drop-in that populates it from free text in seconds.

Where the narration is genuinely ambiguous — e.g. "I said her name and she opened
her eyes, though she may have been waking on her own" — the agent does **not**
guess the GCS eye score. It leaves the field blank and drafts the exact clarifying
question a data manager would need answered. That trades a little completeness to
protect correctness, and the scorecard shows the tradeoff directly.

An independent, deterministic **consistency check** re-verifies the agent's own
output — e.g. it recomputes GCS Eye+Verbal+Motor and confirms the sum matches the
overall Glasgow score the nurse stated aloud.

## Run it

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# optional — real agent instead of the scripted mock:
export ANTHROPIC_API_KEY=sk-...
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000. Pick a sample narration, click **Fill flowsheet →**.
The dropdowns populate, the scorecard scores it, and any flags appear with their
clarifying questions. You can also change any dropdown by hand at any time.

### Mock vs. live

With no `ANTHROPIC_API_KEY` set, the app runs in **mock mode**: the two built-in
sample narrations return scripted agent responses (clearly labeled MOCK AGENT in
the UI), so the whole pipeline is demoable before the key is wired in. Set the key
to run the real Claude agent — then it works on arbitrary pasted text, not just the
samples.

## How it works

- `backend/data/scenarios.json` — the sample narrations (input text only).
- `backend/data/ground_truth.json` — the answer key per scenario (kept server-side;
  used only to score, never shipped to the flowsheet).
- `backend/schema.py` — the legacy flowsheet's field registry: which dropdowns
  exist and their allowed options.
- `backend/agent.py` — the extraction agent. Sends the narration to Claude with a
  structured tool that either charts a field or flags it with a clarifying
  question; falls back to scripted mock responses when there's no API key. Also
  holds `check_consistency`, the deterministic adversarial re-check.
- `backend/eval.py` — scores a fill on completeness / correctness / currency.
- `backend/main.py` — FastAPI: serves the flowsheet and the `POST /api/fill`
  endpoint (narration in → updates + flags + consistency + eval out).
- `frontend/` — plain HTML/JS/CSS (no build step): the legacy dropdown flowsheet on
  the left, the narration box + scorecard + flags panel on the right.

## Known scope cut

Speech-to-text isn't wired in (this machine has no ffmpeg/Whisper), so the input is
transcribed narration text rather than live audio. Swapping in real STT means
feeding its transcript into the same `POST /api/fill` — the agent and eval
downstream don't change.
