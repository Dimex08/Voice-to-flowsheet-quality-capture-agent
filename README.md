# Voice-to-flowsheet-quality-capture-agent

This project focuses on improving nursing workflow through a voice-to-workflow system that also tracks data quality measures for clinical documentation.

## Project overview

We are developing a potentially scalable system that captures ambient clinical information, maps it to nursing flowsheet assessments, and evaluates the quality of that documentation in real time. The goal is to improve how nurses document at the point of care while also monitoring the completeness, correctness, and currency of the mapped observations.

## Problem statement

Evidence suggests that electronic health record (EHR) user interface features influence the quality of clinical data capture. Nurses typically document in a flowsheet, which is a structured template used for entering bedside clinical assessments. Because this workflow often requires manual clicks and navigation, it may not support real-time documentation. Delayed documentation can reduce recall and negatively affect the completeness, correctness, and currency of nursing assessments.

## Proposed solution

This system aims to reduce documentation burden by using voice-based capture of clinical information and mapping that information to the appropriate flowsheet assessment. In addition, it will track data quality measures so that the capture process can be improved over time.

## Where it fits in the clinical workflow

The system inserts at the **gap between assessment and documentation** at the bedside — the point where clinical information is most accurate but least likely to be captured in real time.

**When it's used.** Bedside nursing assessments that map to structured flowsheet fields: shift head-to-toe assessments, scheduled reassessments, and event-driven checks. Serial neuro checks are a concrete high-frequency example — a fall or stroke protocol can require a full Glasgow Coma Scale, pupil, and motor exam repeated every 15–60 minutes, each one currently reconstructed from memory once the nurse reaches a workstation.

**The gap today.** During a hands-on assessment the nurse usually cannot chart in the moment — hands are occupied, attention is on the patient, and a terminal isn't always within reach. The observations are held in memory or jotted on a scrap note, then batch-entered at the nursing station minutes to hours later. That delay is what degrades the **completeness, correctness, and currency** of the record.

**Where this agent sits.** The nurse narrates during or immediately after the assessment. The agent maps that speech onto the discrete flowsheet fields and surfaces it for the nurse to review — **human-in-the-loop by design: the agent proposes, the nurse confirms, edits, or overrides before anything is committed.** It never charts silently. Where the narration is ambiguous, the agent leaves the field blank and drafts the specific question the nurse (or a downstream data manager) needs to resolve, so review effort is focused exactly where it's needed. Because every field stays a manually editable dropdown, the agent layers on top of the existing legacy flowsheet rather than replacing it.

**What it feeds downstream.** Structured flowsheet data drives shift handoff (e.g. SBAR), early-warning scores (e.g. NEWS/MEWS), protocol compliance (fall, stroke, sepsis bundles), and quality and regulatory reporting. Each of those is only as reliable as the flowsheet's completeness, correctness, and currency — which is why capturing the data earlier *and* monitoring its quality both matter.

## Goals

- Improve nursing workflow efficiency at the bedside
- Support real-time or near real-time documentation
- Enhance the completeness, correctness, and currency of flowsheet data
- Create a scalable approach for ambient clinical documentation that is adaptable to legacy systems and data quality monitoring

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
to run the real agent — then it works on arbitrary text, not just the samples.

## How it works

- `backend/data/scenarios.json` — the sample narrations (input text only).
- `backend/data/ground_truth.json` — the answer key per scenario (kept server-side;
  used only to score, never shipped to the flowsheet).
- `backend/schema.py` — the flowsheet's field registry: which dropdowns exist and
  their allowed options.
- `backend/agent.py` — the extraction agent. Sends the narration to Claude with a
  structured tool that either charts a field or flags it with a clarifying
  question; falls back to scripted mock responses when there's no API key. Also
  holds `check_consistency`, the deterministic re-check of the agent's own output
  (e.g. recomputes GCS Eye+Verbal+Motor and confirms the sum matches the stated
  Glasgow total).
- `backend/eval.py` — scores a fill on completeness / correctness / currency.
- `backend/main.py` — FastAPI: serves the flowsheet and the `POST /api/fill`
  endpoint (narration in → updates + flags + consistency + eval out).
- `frontend/` — the flowsheet UI: dropdown fields on the left, the input box +
  quality scorecard + flags panel on the right.
