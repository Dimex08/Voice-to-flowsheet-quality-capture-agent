# Voice-to-Flowsheet Quality Capture Agent

This project focuses on improving nursing workflow through a voice-to-flowsheet system that captures ambient clinical information, maps it to nursing flowsheet assessments, and evaluates the quality of that documentation in real time.

## Project Overview

We are developing a potentially scalable system that captures ambient clinical information, maps it to nursing flowsheet assessments, and evaluates the quality of that documentation in real time. The goal is to improve how nurses document at the point of care while also monitoring the completeness, correctness, and currency of the mapped observations.

## Problem Statement

Evidence suggests that electronic health record (EHR) user interface features influence the quality of clinical data capture. Nurses typically document in a flowsheet, which is a structured template used for entering bedside clinical assessments. Because this workflow often requires manual clicks and navigation, it may not support real-time documentation. Delayed documentation can reduce recall and negatively affect the completeness, correctness, and currency of nursing assessments.

Research also shows that nurses commonly split documentation between partial point-of-care entry and later completion, a workaround that compromises all three data quality dimensions simultaneously.

## Evidence Base

This project is grounded in findings from our published integrative review:

> Madandola OO, Bjarnadottir RI, Yao Y, Ansell M, Dos Santos F, Cho H, Dunn Lopez K, Macieira TGR, Keenan GM. The relationship between electronic health records user interface features and data quality of patient clinical information: an integrative review. *J Am Med Inform Assoc*. 2024;31(1):240-255. doi:10.1093/jamia/ocad188

### Key Findings

- **Currency is the most neglected data quality dimension.** Only 3 of 11 studies assessed currency, yet it is essential for clinical decision-making. Voice-activated charting is identified as a promising approach for enabling real-time documentation at the point of care.
- **Automated algorithmic data capture aids showed the strongest improvements** in both completeness and correctness across studies, reducing clinician cognitive burden through predictive models and auto-suggestions.
- **Standardized terminologies at the UI level enhance correctness** by constraining response sets to systematically developed terms, reducing free-text variability.
- **Mandatory fields improve completeness but increase documentation time**, a tradeoff that voice-based capture could mitigate.
- **Adaptive user interfaces (AUIs) augmented with generative AI** are identified as having great promise for improving data quality, especially for analyzing heterogeneous data and generating context-aware auto-suggestions.

### Data Quality Framework

The project uses the Weiskopf et al. data quality assessment framework with three core dimensions:

- **Completeness**: Whether expected patient data are present in the record
- **Correctness**: Whether captured data are accurate, concordant, and truly reflective of clinical observations
- **Currency**: Whether data were recorded within the appropriate time frame relative to the clinical event

## Proposed Solution

This system aims to reduce documentation burden by using voice-based capture of clinical information and mapping that information to the appropriate flowsheet assessment. It addresses the key evidence gaps by:

1. Enabling real-time documentation to improve currency
2. Using automated algorithmic aids (NLP and LLM-based mapping) to improve completeness, and correctness
3. Mapping voice input to standardized terminologies to enhance data consistency
4. Tracking data quality measures across all three dimensions so that the capture process can be evaluated and improved over time

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
