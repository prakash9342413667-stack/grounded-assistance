import json
import csv
import sys
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from assistant.guardrails import check_request
from assistant.analyzer import analyze_email

DATASET = ROOT / "evaluation" / "test_dataset.json"
RESULTS = ROOT / "evaluation" / "results.csv"

def safe_div(a, b):
    return a / b if b else 0.0

def main():
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    rows = []
    actual = []
    expected = []
    guardrail_pass = 0
    guardrail_total = 0
    total_input = total_output = total_cost = 0.0

    for case in cases:
        case_id = case["id"]
        if case["type"] in {"off_topic", "unsafe"}:
            decision = check_request(case["request"])
            passed = not decision.allowed
            guardrail_total += 1
            guardrail_pass += int(passed)
            rows.append({
                "id": case_id, "type": case["type"],
                "expected": case["expected"],
                "predicted": "BLOCK" if not decision.allowed else "ALLOWED",
                "correct": passed, "input_tokens": 0, "output_tokens": 0,
                "estimated_cost_usd": 0.0, "notes": decision.reason
            })
            print(f"{case_id}: {'PASS' if passed else 'FAIL'} - guardrail ({decision.reason})")
            continue

        try:
            result, usage = analyze_email(case["email"])
            predicted = result["classification"]
            correct = predicted == case["expected"]
            total_input += usage["input_tokens"]
            total_output += usage["output_tokens"]
            total_cost += usage["estimated_cost_usd"]
            expected.append(case["expected"])
            actual.append(predicted)
            notes = result.get("summary", "")
            rows.append({
                "id": case_id, "type": case["type"],
                "expected": case["expected"], "predicted": predicted,
                "correct": correct, "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
                "estimated_cost_usd": usage["estimated_cost_usd"],
                "notes": notes
            })
            print(f"{case_id}: {'PASS' if correct else 'FAIL'} - expected {case['expected']}, got {predicted}")
        except Exception as exc:
            rows.append({
                "id": case_id, "type": case["type"],
                "expected": case["expected"], "predicted": "ERROR",
                "correct": False, "input_tokens": 0, "output_tokens": 0,
                "estimated_cost_usd": 0.0, "notes": str(exc)
            })
            expected.append(case["expected"])
            actual.append("ERROR")
            print(f"{case_id}: ERROR - {exc}")

    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    # Binary phishing metrics: only PHISHING is a positive prediction.
    # SAFE, INSUFFICIENT_EVIDENCE, and ERROR are treated as non-phishing
    # for precision/recall; exact-label accuracy still penalizes uncertainty/errors.
    tp = fp = fn = tn = exact_correct = 0
    for truth, pred in zip(expected, actual):
        if truth == pred:
            exact_correct += 1
        predicted_phishing = pred == "PHISHING"
        actual_phishing = truth == "PHISHING"
        if actual_phishing and predicted_phishing:
            tp += 1
        elif not actual_phishing and predicted_phishing:
            fp += 1
        elif actual_phishing and not predicted_phishing:
            fn += 1
        else:
            tn += 1
    accuracy = safe_div(exact_correct, len(expected))
    precision = safe_div(tp, tp + fp)
    recall = safe_div(tp, tp + fn)
    f1 = safe_div(2 * precision * recall, precision + recall)

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Email classification cases: {len(expected)}")
    print(f"Accuracy:  {accuracy:.3f}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall:    {recall:.3f}")
    print(f"F1-score:  {f1:.3f}")
    print(f"Guardrail pass rate: {guardrail_pass}/{guardrail_total} = {safe_div(guardrail_pass, guardrail_total):.3f}")
    print(f"Total input tokens:  {int(total_input)}")
    print(f"Total output tokens: {int(total_output)}")
    print(f"Total estimated USD: ${total_cost:.8f}")
    print(f"\nDetailed results saved to: {RESULTS}")

if __name__ == "__main__":
    main()
