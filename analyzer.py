import json
import time
import random

import httpx

from google import genai
from google.genai import types, errors

from config import (
    GEMINI_API_KEY, MODEL_NAME, FALLBACK_MODEL,
    INPUT_USD_PER_MILLION, OUTPUT_USD_PER_MILLION
)
from assistant.prompts import build_prompt

RETRYABLE_CODES = {429, 500, 502, 503, 504}


def _client():
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your local .env file."
        )
    return genai.Client(
        api_key=GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=60_000),  # 60 s per request
    )


def _get_usage(response):
    meta = getattr(response, "usage_metadata", None)
    input_tokens = int(getattr(meta, "prompt_token_count", 0) or 0)
    # Thinking tokens are billed as output but reported separately.
    output_tokens = int(getattr(meta, "candidates_token_count", 0) or 0) \
        + int(getattr(meta, "thoughts_token_count", 0) or 0)
    total_tokens = int(getattr(meta, "total_token_count", 0) or (input_tokens + output_tokens))

    estimated_cost = (
        input_tokens * INPUT_USD_PER_MILLION / 1_000_000
        + output_tokens * OUTPUT_USD_PER_MILLION / 1_000_000
    )
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost_usd": estimated_cost,
    }


def _generate_with_retry(client, contents, config, max_attempts=5):
    """Retry on overload/rate-limit errors, then try the fallback model."""
    models = [MODEL_NAME]
    if FALLBACK_MODEL and FALLBACK_MODEL != MODEL_NAME:
        models.append(FALLBACK_MODEL)

    last_exc = None
    for model in models:
        for attempt in range(max_attempts):
            try:
                return client.models.generate_content(
                    model=model, contents=contents, config=config
                )
            except errors.APIError as exc:
                last_exc = exc
                if getattr(exc, "code", None) not in RETRYABLE_CODES:
                    raise  # bad key / bad request: retrying won't help
                time.sleep(2 ** attempt + random.random())  # ~1s, 2s, 4s, 8s, 16s
            except (httpx.TransportError, ConnectionError, TimeoutError) as exc:
                # Dropped connection, "Server disconnected", timeouts, DNS blips
                last_exc = exc
                time.sleep(2 ** attempt + random.random())
    raise last_exc


def _norm(text: str) -> str:
    return " ".join(str(text).split()).casefold()


def analyze_email(email_text: str):
    client = _client()

    schema = {
        "type": "OBJECT",
        "properties": {
            "classification": {
                "type": "STRING",
                "enum": ["SAFE", "PHISHING", "INSUFFICIENT_EVIDENCE"]
            },
            "risk_level": {
                "type": "STRING",
                "enum": ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
            },
            "summary": {"type": "STRING"},
            "evidence": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "indicator": {"type": "STRING"},
                        "quote": {"type": "STRING"}
                    },
                    "required": ["indicator", "quote"]
                }
            },
            "recommended_action": {"type": "STRING"},
            "limitations": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        },
        "required": [
            "classification", "risk_level", "summary",
            "evidence", "recommended_action", "limitations"
        ]
    }

    response = _generate_with_retry(
        client,
        contents=build_prompt(email_text),
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.1,
            max_output_tokens=2048,
        ),
    )

    if not response.text:
        raise RuntimeError("The model returned an empty response.")

    result = json.loads(response.text)

    # Enforce exact-quote grounding after generation (whitespace-normalized).
    verified_evidence = []
    email_norm = _norm(email_text)
    for item in result.get("evidence", []):
        quote = str(item.get("quote", "")).strip()
        if quote and _norm(quote) in email_norm:
            verified_evidence.append({
                "indicator": str(item.get("indicator", "Email indicator")),
                "quote": quote
            })
    result["evidence"] = verified_evidence

    if result.get("classification") not in {"SAFE", "PHISHING", "INSUFFICIENT_EVIDENCE"}:
        result["classification"] = "INSUFFICIENT_EVIDENCE"
    if result.get("risk_level") not in {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}:
        result["risk_level"] = "UNKNOWN"

    return result, _get_usage(response)