# Grounded AI Phishing Email Security Assistant

A Streamlit application that analyzes email text for phishing indicators using Gemini. It includes deterministic request guardrails, evidence-quote validation, an evaluation dataset, scored results, and token/cost tracking.

## Features

- Classifies email as `SAFE`, `PHISHING`, or `INSUFFICIENT_EVIDENCE`.
- Returns a risk level, explanation, exact evidence excerpts, and recommended action.
- Blocks off-topic requests and clearly unsafe requests before making an API call.
- Treats email content as untrusted input (prompt-injection resistant design).
- Validates that evidence quotes actually occur in the supplied email.
- Records input/output/total tokens and estimates API cost.
- Evaluates 20 email examples and 10 guardrail examples.

## Requirements

- Python 3.11 or newer
- Gemini API key from Google AI Studio
- Internet connection for Gemini API calls

## Setup (Windows PowerShell)

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and replace `put_your_api_key_here` with your Gemini API key. Never upload `.env` to GitHub.

## Run the application

```powershell
streamlit run app.py
```

Streamlit will display a local URL, usually `http://localhost:8501`.

## Run the evaluation

The evaluation sends the 20 email cases to Gemini and checks the 10 off-topic/unsafe cases locally.

```powershell
python evaluation\evaluate.py
```

Detailed results are written to `evaluation/results.csv`. The terminal reports accuracy, precision, recall, F1-score, guardrail pass rate, token usage, and estimated cost.

The evaluation requires a valid API key and may consume API quota. Run it after changing prompts or model settings. Do not manually invent or edit scores: preserve the generated CSV as the experiment output.

## Evaluation definitions

- **Accuracy:** correct SAFE/PHISHING predictions divided by all email classification cases.
- **Precision:** true phishing predictions divided by all predicted phishing cases.
- **Recall:** detected phishing cases divided by all actual phishing cases.
- **F1:** harmonic mean of precision and recall.
- **Guardrail pass rate:** blocked off-topic/unsafe test requests divided by all guardrail test requests.

`INSUFFICIENT_EVIDENCE` and API errors count as incorrect for the binary email benchmark. This is intentionally strict.

## Token and cost measurement

Token counts come from Gemini response usage metadata. Estimated cost is calculated from the configurable per-million-token rates in `config.py` / `.env`. It is a paid-tier equivalent estimate, not an invoice. Free-tier availability, model pricing, and billing can change; check Google's pricing page before reporting cost.

## Safety limitations

- This is an educational assistant, not a replacement for an organization's email gateway or security team.
- `SAFE` means no clear phishing indicators were found in the provided text; it is not a guarantee.
- Text-only inspection cannot verify live sender reputation, DNS records, URLs, or attachment contents.
- Do not paste passwords, OTPs, private keys, or confidential personal data.
- The local keyword guardrails are intentionally simple and can have false positives/negatives. Improve them with more tests before production use.

## Repository structure

```text
grounded-phishing-assistant/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── assistant/
│   ├── __init__.py
│   ├── analyzer.py
│   ├── guardrails.py
│   └── prompts.py
└── evaluation/
    ├── test_dataset.json
    └── evaluate.py
```

## Suggested experiment record

After running evaluation, add the actual generated metrics and date to this README or a separate `evaluation/REPORT.md`. Include model name, dataset size, prompt version, and token/cost totals. Never claim a score before running the evaluation.

## Model and pricing references

- Gemini API documentation: https://ai.google.dev/gemini-api/docs
- Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing
