import csv
import json
import traceback
from pathlib import Path
from typing import Any

from config import AppConfig
from main_llm import build_analyzer, predict_video


VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv"}


FOLDER_LABEL_MAP = {
    "zero (Zero)": 0,
    "drive (Attack)": 1,
    "counter drive (Attack)": 2,
    "smash (Attack)": 3,
    "backhand twist (Attack)": 4,
    "fast drive (Attack)": 5,
    "fast push (Attack)": 6,
    "flip (Attack)": 7,
    "pimple’s long push (Control)": 8,
    "pimple's long push (Control)": 8,
    "pimple’s fast push (Control)": 9,
    "pimple's fast push (Control)": 9,
    "long push (Control)": 10,
    "drop shot (Control)": 11,
    "chop (Defensive)": 12,
    "block (Defensive)": 13,
    "lob (Defensive)": 14,
    "traditional (Serve)": 15,
    "hook (Serve)": 16,
    "reverse (Serve)": 17,
    "squat (Serve)": 18,
}


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


CSV_FIELDS = [
    # Basic identifiers
    "video_name",
    "video_path",
    "class_folder",

    # Ground truth
    "ground_truth_label",
    "ground_truth_name",

    # Experiment setup
    "provider",
    "model_name",
    "prompt_version",
    "prompt_path",
    "action_guide_path",

    # Prediction
    "predicted_label",
    "predicted_name_zh",
    "predicted_name_en",
    "predicted_type",
    "coarse_category",
    "derived_coarse_category",
    "coarse_category_consistent",
    "main_actor",
    "observed_evidence",
    "decision_reason",
    "closest_alternative",
    "alternative_reason",
    "confidence",

    # Parsing / validity
    "parse_success",
    "parse_error",

    # Evaluation
    "correct",

    # Timing
    "inference_sec",

    # Usage / cost
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "cost_usd",

    # Video / frame info
    "fps",
    "frame_count",
    "sampled_frame_count",
    "duration_sec",
    "width",
    "height",
    "sampled_frame_indices",

    # API metadata
    "response_id",

    # Output / run status
    "json_path",
    "status",
    "error",
]


def find_labeled_videos(input_path: Path) -> list[dict[str, Any]]:
    """
    Supports two structures:

    1. Class-folder dataset:
       test_samples_10/<class name>/*.mp4

    2. Single flat folder or single file:
       In this case ground_truth_label will be blank.
    """
    if input_path.is_file():
        return [{
            "video_path": input_path,
            "class_folder": "",
            "ground_truth_label": "",
            "ground_truth_name": "",
        }]

    if not input_path.is_dir():
        raise FileNotFoundError(f"Input path not found: {input_path}")

    samples: list[dict[str, Any]] = []

    class_dirs = [p for p in sorted(input_path.iterdir()) if p.is_dir()]
    has_known_class_dir = any(p.name in FOLDER_LABEL_MAP for p in class_dirs)

    if has_known_class_dir:
        for class_dir in class_dirs:
            if class_dir.name not in FOLDER_LABEL_MAP:
                print(f"[WARN] Skip unknown class folder: {class_dir.name}")
                continue

            gt_label = FOLDER_LABEL_MAP[class_dir.name]

            for video_path in sorted(class_dir.iterdir()):
                if (
                    video_path.is_file()
                    and video_path.suffix.lower() in VIDEO_EXTS
                ):
                    samples.append({
                        "video_path": video_path,
                        "class_folder": class_dir.name,
                        "ground_truth_label": gt_label,
                        "ground_truth_name": LABEL_NAME[gt_label],
                    })

        return samples

    for video_path in sorted(input_path.iterdir()):
        if (
            video_path.is_file()
            and video_path.suffix.lower() in VIDEO_EXTS
        ):
            samples.append({
                "video_path": video_path,
                "class_folder": "",
                "ground_truth_label": "",
                "ground_truth_name": "",
            })

    return samples


def load_existing_rows(
    csv_path: Path,
) -> dict[str, dict[str, str]]:
    if not csv_path.exists():
        return {}

    rows: dict[str, dict[str, str]] = {}

    with csv_path.open(
        "r",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            video_path = row.get("video_path", "")

            if video_path:
                rows[video_path] = row

    return rows


def write_predictions_csv(
    csv_path: Path,
    rows: list[dict[str, Any]],
) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore",
        )

        writer.writeheader()
        writer.writerows(rows)


def make_json_path(
    output_dir: Path,
    sample: dict[str, Any],
    config: AppConfig,
) -> Path:
    video_path: Path = sample["video_path"]
    class_folder = sample.get("class_folder", "")

    if class_folder:
        json_dir = output_dir / class_folder
    else:
        json_dir = output_dir

    json_dir.mkdir(parents=True, exist_ok=True)

    return (
        json_dir
        / f"{video_path.stem}{config.llm.output_json_suffix}"
    )


def serialize_list(value: Any) -> str:
    """
    Lists are stored as JSON strings inside CSV cells.
    """
    if value is None:
        return ""

    if isinstance(value, list):
        return json.dumps(
            value,
            ensure_ascii=False,
        )

    return str(value)


def build_success_row(
    sample: dict[str, Any],
    result: dict[str, Any],
    json_path: Path,
) -> dict[str, Any]:
    video_path: Path = sample["video_path"]

    prediction = result.get("prediction", {})
    experiment_info = result.get("experiment_info", {})
    timing = result.get("timing", {})
    usage = result.get("usage", {})
    video_info = result.get("video_info", {})

    predicted_label = prediction.get("predicted_label")
    gt_label = sample.get("ground_truth_label", "")

    parse_success = prediction.get(
        "parse_success",
        False,
    )

    correct: int | str = ""

    if (
        parse_success
        and gt_label != ""
        and predicted_label is not None
    ):
        correct = int(
            int(predicted_label) == int(gt_label)
        )

    # API call succeeded but response could not be parsed.
    status = "ok" if parse_success else "parse_error"

    return {
        "video_name": video_path.name,
        "video_path": str(video_path),
        "class_folder": sample.get(
            "class_folder",
            "",
        ),

        "ground_truth_label": gt_label,
        "ground_truth_name": sample.get(
            "ground_truth_name",
            "",
        ),

        "provider": experiment_info.get(
            "provider",
            "",
        ),
        "model_name": experiment_info.get(
            "model_name",
            "",
        ),
        "prompt_version": experiment_info.get(
            "prompt_version",
            "",
        ),
        "prompt_path": experiment_info.get(
            "prompt_path",
            "",
        ),
        "action_guide_path": experiment_info.get(
            "action_guide_path",
            "",
        ),

        "predicted_label": (
            predicted_label
            if predicted_label is not None
            else ""
        ),
        "predicted_name_zh": prediction.get(
            "predicted_name_zh",
            "",
        ) or "",
        "predicted_name_en": prediction.get(
            "predicted_name_en",
            "",
        ) or "",
        "predicted_type": prediction.get(
            "predicted_type",
            "",
        ) or "",
        "coarse_category": prediction.get(
            "coarse_category",
            "",
        ) or "",
        "derived_coarse_category": prediction.get(
            "derived_coarse_category",
            "",
        ) or "",
        "coarse_category_consistent": prediction.get(
            "coarse_category_consistent",
            "",
        ),
        "main_actor": prediction.get(
            "main_actor",
            "",
        ) or "",
        "observed_evidence": serialize_list(
            prediction.get("observed_evidence", [])
        ),
        "decision_reason": prediction.get(
            "decision_reason",
            "",
        ) or "",
        "closest_alternative": (
            prediction.get("closest_alternative")
            if prediction.get("closest_alternative") is not None
            else ""
        ),
        "alternative_reason": prediction.get(
            "alternative_reason",
            "",
        ) or "",
        "confidence": (
            prediction.get("confidence")
            if prediction.get("confidence") is not None
            else ""
        ),

        "parse_success": parse_success,
        "parse_error": prediction.get(
            "parse_error",
            "",
        ) or "",

        "correct": correct,

        "inference_sec": timing.get(
            "inference_sec",
            "",
        ),

        "input_tokens": usage.get(
            "input_tokens",
            "",
        ),
        "output_tokens": usage.get(
            "output_tokens",
            "",
        ),
        "total_tokens": usage.get(
            "total_tokens",
            "",
        ),
        "cost_usd": usage.get(
            "cost_usd",
            "",
        ),

        "fps": video_info.get("fps", ""),
        "frame_count": video_info.get(
            "frame_count",
            "",
        ),
        "sampled_frame_count": video_info.get(
            "sampled_frame_count",
            "",
        ),
        "duration_sec": video_info.get(
            "duration_sec",
            "",
        ),
        "width": video_info.get("width", ""),
        "height": video_info.get("height", ""),
        "sampled_frame_indices": serialize_list(
            video_info.get(
                "sampled_frame_indices",
                [],
            )
        ),

        "response_id": result.get(
            "response_id",
            "",
        ) or "",

        "json_path": str(json_path),
        "status": status,
        "error": "",
    }


def build_error_row(
    sample: dict[str, Any],
    json_path: Path,
    error: str,
) -> dict[str, Any]:
    video_path: Path = sample["video_path"]

    row = {
        field: ""
        for field in CSV_FIELDS
    }

    row.update({
        "video_name": video_path.name,
        "video_path": str(video_path),
        "class_folder": sample.get(
            "class_folder",
            "",
        ),
        "ground_truth_label": sample.get(
            "ground_truth_label",
            "",
        ),
        "ground_truth_name": sample.get(
            "ground_truth_name",
            "",
        ),
        "parse_success": False,
        "json_path": str(json_path),
        "status": "error",
        "error": error,
    })

    return row


def main():
    config = AppConfig()

    input_path = Path(
        config.video.input_video_path
    )

    output_dir = config.output_dir_path
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    csv_path = output_dir / "predictions.csv"

    samples = find_labeled_videos(
        input_path
    )

    if not samples:
        raise RuntimeError(
            f"No video files found in: {input_path}"
        )

    print(
        f"[INFO] input_path : {input_path}"
    )
    print(
        f"[INFO] output_dir : {output_dir}"
    )
    print(
        f"[INFO] total videos: {len(samples)}"
    )

    existing = load_existing_rows(
        csv_path
    )

    rows: list[dict[str, Any]] = []

    analyzer = build_analyzer(config)

    for idx, sample in enumerate(
        samples,
        start=1,
    ):
        video_path: Path = sample[
            "video_path"
        ]

        video_key = str(video_path)

        json_path = make_json_path(
            output_dir,
            sample,
            config,
        )

        old_row = existing.get(video_key)

        # Only skip truly valid previous results.
        if (
            old_row
            and old_row.get("status") == "ok"
            and old_row.get("parse_success", "").lower()
            in {"true", "1"}
            and Path(
                old_row.get(
                    "json_path",
                    "",
                )
            ).exists()
        ):
            print(
                f"[{idx}/{len(samples)}] "
                f"[SKIP] {video_path.name}"
            )

            rows.append(old_row)
            continue

        print("=" * 80)
        print(
            f"[{idx}/{len(samples)}] "
            f"Processing: {video_path}"
        )

        try:
            result = predict_video(
                video_path=video_path,
                config=config,
                analyzer=analyzer,
                save_json=True,
                output_json_path=json_path,
            )

            row = build_success_row(
                sample=sample,
                result=result,
                json_path=json_path,
            )

            if row["status"] == "ok":
                print(
                    f"[PRED] "
                    f"{row['predicted_label']} "
                    f"{row['predicted_name_en']}"
                )

                if row["correct"] != "":
                    print(
                        f"[GT]   "
                        f"{row['ground_truth_label']} "
                        f"{row['ground_truth_name']}"
                    )

                    print(
                        f"[RESULT] "
                        f"{'correct' if row['correct'] else 'wrong'}"
                    )
            else:
                print(
                    f"[PARSE ERROR] "
                    f"{video_path.name}"
                )

                print(
                    row["parse_error"]
                )

            print(
                f"[TIME] "
                f"{row['inference_sec']} sec"
            )

            print(
                f"[TOKENS] "
                f"in={row['input_tokens']} "
                f"out={row['output_tokens']} "
                f"total={row['total_tokens']}"
            )

            print(
                f"[COST] "
                f"${row['cost_usd']}"
            )

        except Exception:
            err = traceback.format_exc()

            print(
                f"[ERROR] "
                f"{video_path.name}"
            )
            print(err)

            row = build_error_row(
                sample=sample,
                json_path=json_path,
                error=err,
            )

        rows.append(row)

        # Save after every video to preserve progress.
        write_predictions_csv(
            csv_path,
            rows,
        )

    write_predictions_csv(
        csv_path,
        rows,
    )

    print("=" * 80)
    print(
        "[DONE] Saved batch predictions to: "
        f"{csv_path}"
    )


if __name__ == "__main__":
    main()
