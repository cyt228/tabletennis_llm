import csv
from pathlib import Path


PREDICTIONS_PATH = Path("data/outputs/predictions.csv")
GT_PATH = Path("data/gt.csv")
OUTPUT_PATH = Path("data/outputs/evaluation.csv")


def load_csv_as_dict(path: Path, key_field: str) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    data = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row[key_field].strip()
            data[key] = row
    return data


def safe_int(value, default=-999):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def main():
    predictions = load_csv_as_dict(PREDICTIONS_PATH, "video_name")
    gt = load_csv_as_dict(GT_PATH, "video_name")

    matched_names = sorted(set(predictions.keys()) & set(gt.keys()))

    rows = []
    correct_count = 0

    for video_name in matched_names:
        pred_label = safe_int(predictions[video_name].get("predicted_label"))
        gt_label = safe_int(gt[video_name].get("ground_truth"))
        correct = int(pred_label == gt_label)

        if correct:
            correct_count += 1

        rows.append({
            "video_name": video_name,
            "ground_truth": gt_label,
            "predicted_label": pred_label,
            "correct": correct,
        })

    total = len(rows)
    accuracy = correct_count / total if total > 0 else 0.0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["video_name", "ground_truth", "predicted_label", "correct"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print("=== Evaluation Result ===")
    print(f"total: {total}")
    print(f"correct: {correct_count}")
    print(f"accuracy: {accuracy:.4f}")
    print(f"[DONE] saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()