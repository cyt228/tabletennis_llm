import csv
from pathlib import Path
from collections import defaultdict
from statistics import mean

from config import AppConfig


LABEL_NAME = {
    0: "zero",
    1: "drive",
    2: "counter drive",
    3: "smash",
    4: "backhand twist",
    5: "fast drive",
    6: "fast push",
    7: "flip",
    8: "pimple’s long push",
    9: "pimple’s fast push",
    10: "long push",
    11: "drop shot",
    12: "chop",
    13: "block",
    14: "lob",
    15: "traditional",
    16: "hook",
    17: "reverse",
    18: "squat",
}

BIG_TYPE_NAME = {
    "Zero": "zero",
    "Attack": "attack",
    "Control": "control",
    "Defensive": "defensive",
    "Serve": "serve",
}

DETAILED_LABELS = list(range(19))
BIG_TYPE_LABELS = ["Zero", "Attack", "Control", "Defensive", "Serve"]


# -----------------------------
# Basic helpers
# -----------------------------

def label_to_big_type(label: int | None) -> str:
    if label is None:
        return "Unknown"
    if label == 0:
        return "Zero"
    if 1 <= label <= 7:
        return "Attack"
    if 8 <= label <= 11:
        return "Control"
    if 12 <= label <= 14:
        return "Defensive"
    if 15 <= label <= 18:
        return "Serve"
    return "Unknown"


def safe_int(value, default=None):
    try:
        if value in ("", None):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(value, default=None):
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_div(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def read_predictions(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Predictions file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row.keys():
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)

    if not fieldnames:
        fieldnames = ["empty"]

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def first_number(row: dict, *keys: str) -> float | None:
    """Read the first numeric value found among possible column aliases."""
    for key in keys:
        value = safe_float(row.get(key))
        if value is not None:
            return value
    return None


def values_present(rows: list[dict], key: str) -> list[float]:
    values = []
    for row in rows:
        value = safe_float(row.get(key))
        if value is not None:
            values.append(value)
    return values


def fmt(value: float | None, digits=6):
    return "" if value is None else f"{value:.{digits}f}"


# -----------------------------
# Metrics
# -----------------------------

def new_confusion(labels):
    return {
        gt: {pred: 0 for pred in labels}
        for gt in labels
    }


def build_prf_rows(confusion: dict, labels: list, label_name_func) -> list[dict]:
    rows = []

    for label in labels:
        tp = confusion[label][label]
        support = sum(confusion[label][pred] for pred in labels)
        predicted_total = sum(confusion[gt][label] for gt in labels)

        precision = safe_div(tp, predicted_total)
        recall = safe_div(tp, support)
        f1 = safe_div(2 * precision * recall, precision + recall)

        rows.append({
            "label": label,
            "label_name": label_name_func(label),
            "support": support,
            "correct": tp,
            "predicted_total": predicted_total,
            "precision": f"{precision:.6f}",
            "recall": f"{recall:.6f}",
            "f1": f"{f1:.6f}",
        })

    return rows


def build_confusion_rows(confusion: dict, labels: list, label_name_func) -> list[dict]:
    rows = []

    for gt in labels:
        row = {
            "ground_truth": f"{gt}_{label_name_func(gt)}"
            if isinstance(gt, int)
            else str(gt)
        }

        for pred in labels:
            pred_name = label_name_func(pred)
            row[f"pred_{pred}_{pred_name}" if isinstance(pred, int) else f"pred_{pred}"] = confusion[gt][pred]

        rows.append(row)

    return rows


# -----------------------------
# Main evaluation
# -----------------------------

def main():
    config = AppConfig()

    output_dir = config.output_dir_path
    predictions_path = output_dir / "predictions.csv"
    eval_dir = output_dir / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)

    rows = read_predictions(predictions_path)

    evaluated = []
    failed_rows = []
    error_rows = []

    detailed_confusion = new_confusion(DETAILED_LABELS)
    big_type_confusion = new_confusion(BIG_TYPE_LABELS)

    for row in rows:
        if row.get("status") != "ok":
            failed_rows.append(row)
            continue

        gt = safe_int(row.get("ground_truth_label"))
        pred = safe_int(row.get("predicted_label"))

        # Cannot evaluate without GT or prediction.
        if gt is None or pred is None:
            continue

        gt_big_type = label_to_big_type(gt)
        pred_big_type = label_to_big_type(pred)

        detailed_correct = int(gt == pred)
        big_type_correct = int(gt_big_type == pred_big_type)

        eval_row = dict(row)
        eval_row.update({
            "detailed_correct": detailed_correct,
            "big_type_gt": gt_big_type,
            "big_type_pred": pred_big_type,
            "big_type_correct": big_type_correct,

            # Normalize usage fields so later analysis uses consistent names.
            # These are aggregated only if the inference pipeline actually saved them.
            "input_tokens": first_number(
                row,
                "input_tokens",
                "prompt_tokens",
                "usage_input_tokens",
            ),
            "output_tokens": first_number(
                row,
                "output_tokens",
                "completion_tokens",
                "usage_output_tokens",
            ),
            "total_tokens": first_number(
                row,
                "total_tokens",
                "usage_total_tokens",
            ),
            "cost_usd": first_number(
                row,
                "cost_usd",
                "cost",
                "usage_cost",
                "total_cost",
            ),
            "inference_time_sec": first_number(
                row,
                "inference_time_sec",
                "latency_sec",
                "elapsed_sec",
                "elapsed_time",
            ),
        })

        # If total_tokens was not explicitly stored but both components exist,
        # derive it without estimating anything else.
        if (
            eval_row["total_tokens"] is None
            and eval_row["input_tokens"] is not None
            and eval_row["output_tokens"] is not None
        ):
            eval_row["total_tokens"] = (
                eval_row["input_tokens"] + eval_row["output_tokens"]
            )

        evaluated.append(eval_row)

        if gt in DETAILED_LABELS and pred in DETAILED_LABELS:
            detailed_confusion[gt][pred] += 1

        if gt_big_type in BIG_TYPE_LABELS and pred_big_type in BIG_TYPE_LABELS:
            big_type_confusion[gt_big_type][pred_big_type] += 1

        if not detailed_correct:
            error_type = (
                "cross_big_type"
                if not big_type_correct
                else "within_big_type"
            )
            error_row = dict(eval_row)
            error_row["error_type"] = error_type
            error_rows.append(error_row)

    # -------------------------
    # Overall accuracy
    # -------------------------

    total = len(evaluated)
    detailed_correct_count = sum(r["detailed_correct"] for r in evaluated)
    big_type_correct_count = sum(r["big_type_correct"] for r in evaluated)

    detailed_accuracy = safe_div(detailed_correct_count, total)
    big_type_accuracy = safe_div(big_type_correct_count, total)

    # -------------------------
    # Efficiency / cost
    # -------------------------

    input_tokens = values_present(evaluated, "input_tokens")
    output_tokens = values_present(evaluated, "output_tokens")
    total_tokens = values_present(evaluated, "total_tokens")
    costs = values_present(evaluated, "cost_usd")
    times = values_present(evaluated, "inference_time_sec")

    summary = {
        "prediction_rows": len(rows),
        "evaluated_total": total,
        "failed_rows": len(failed_rows),

        "detailed_correct": detailed_correct_count,
        "detailed_accuracy": f"{detailed_accuracy:.6f}",

        "big_type_correct": big_type_correct_count,
        "big_type_accuracy": f"{big_type_accuracy:.6f}",

        # Token statistics
        "usage_rows_with_tokens": len(total_tokens),
        "total_input_tokens": fmt(sum(input_tokens), 0) if input_tokens else "",
        "avg_input_tokens": fmt(mean(input_tokens), 2) if input_tokens else "",
        "total_output_tokens": fmt(sum(output_tokens), 0) if output_tokens else "",
        "avg_output_tokens": fmt(mean(output_tokens), 2) if output_tokens else "",
        "total_tokens": fmt(sum(total_tokens), 0) if total_tokens else "",
        "avg_total_tokens": fmt(mean(total_tokens), 2) if total_tokens else "",

        # Cost statistics
        "usage_rows_with_cost": len(costs),
        "total_cost_usd": fmt(sum(costs), 8) if costs else "",
        "avg_cost_usd": fmt(mean(costs), 8) if costs else "",

        # Time statistics
        "usage_rows_with_time": len(times),
        "total_inference_time_sec": fmt(sum(times), 3) if times else "",
        "avg_inference_time_sec": fmt(mean(times), 3) if times else "",
    }

    # -------------------------
    # Class metrics
    # -------------------------

    detailed_metrics = build_prf_rows(
        detailed_confusion,
        DETAILED_LABELS,
        lambda x: LABEL_NAME[x],
    )

    big_type_metrics = build_prf_rows(
        big_type_confusion,
        BIG_TYPE_LABELS,
        lambda x: BIG_TYPE_NAME[x],
    )

    detailed_confusion_rows = build_confusion_rows(
        detailed_confusion,
        DETAILED_LABELS,
        lambda x: LABEL_NAME[x],
    )

    big_type_confusion_rows = build_confusion_rows(
        big_type_confusion,
        BIG_TYPE_LABELS,
        lambda x: BIG_TYPE_NAME[x],
    )

    # -------------------------
    # Output files
    # -------------------------
    #
    # Keep only files that are useful for:
    # 1. reporting,
    # 2. per-class diagnosis,
    # 3. error / evidence inspection,
    # 4. failed-request inspection.
    #

    write_csv(
        eval_dir / "summary.csv",
        [summary],
        list(summary.keys()),
    )

    write_csv(
        eval_dir / "class_metrics_19.csv",
        detailed_metrics,
        ["label", "label_name", "support", "correct",
         "predicted_total", "precision", "recall", "f1"],
    )

    write_csv(
        eval_dir / "class_metrics_5.csv",
        big_type_metrics,
        ["label", "label_name", "support", "correct",
         "predicted_total", "precision", "recall", "f1"],
    )

    write_csv(
        eval_dir / "confusion_matrix_19.csv",
        detailed_confusion_rows,
    )

    write_csv(
        eval_dir / "confusion_matrix_5.csv",
        big_type_confusion_rows,
    )

    # Most important observation file:
    # keeps original model outputs (evidence, rationale, confidence, etc.)
    # plus GT / prediction correctness and normalized usage fields.
    write_csv(
        eval_dir / "samples.csv",
        evaluated,
    )

    # Only incorrect 19-class cases.
    # error_type distinguishes:
    # - within_big_type: coarse class correct, fine class wrong
    # - cross_big_type: even coarse class is wrong
    write_csv(
        eval_dir / "errors.csv",
        error_rows,
    )

    write_csv(
        eval_dir / "failed.csv",
        failed_rows,
    )

    print("=== Evaluation Result ===")
    print(f"predictions           : {predictions_path}")
    print(f"evaluated total       : {total}")
    print(f"detailed correct 0-18 : {detailed_correct_count}")
    print(f"detailed accuracy     : {detailed_accuracy:.4f}")
    print(f"big type correct      : {big_type_correct_count}")
    print(f"big type accuracy     : {big_type_accuracy:.4f}")
    print(f"failed rows           : {len(failed_rows)}")

    if total_tokens:
        print(f"avg total tokens      : {mean(total_tokens):.2f}")
    if times:
        print(f"avg inference time    : {mean(times):.3f} sec")
    if costs:
        print(f"total cost            : ${sum(costs):.8f}")
        print(f"avg cost              : ${mean(costs):.8f}")

    print(f"[DONE] saved to       : {eval_dir}")


if __name__ == "__main__":
    main()