# sample_10_per_action.py

from pathlib import Path
import csv
import random

# ====== 你只需要確認這兩個路徑 ======
ROOT = Path(r"D:\offline_agent\combined")
SEGMENTS_DIR = ROOT / "segments"
SAMPLES_DIR = ROOT / "samples"

N_PER_CLASS = 10
SEED = 42
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
    "sample_id",
    "action_type",
    "ground_truth_label",
    "ground_truth_name",
    "filename",
    "video_path",
    "seed",
    "sample_index_in_class",
]


def main() -> None:
    if not SEGMENTS_DIR.exists():
        raise FileNotFoundError(f"Segments folder not found: {SEGMENTS_DIR}")

    random.seed(SEED)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    global_index = 1

    for class_dir in sorted(SEGMENTS_DIR.iterdir()):
        if not class_dir.is_dir():
            continue

        videos = [
            p for p in class_dir.iterdir()
            if p.is_file() and p.suffix.lower() in VIDEO_EXTS
        ]

        if len(videos) == 0:
            print(f"[SKIP] {class_dir.name}: no videos")
            continue

        sample_count = min(N_PER_CLASS, len(videos))
        sampled = random.sample(videos, sample_count)

        gt_label = FOLDER_LABEL_MAP.get(class_dir.name, "")
        gt_name = LABEL_NAME.get(gt_label, "") if gt_label != "" else ""

        for class_sample_index, src in enumerate(sampled, start=1):
            rows.append({
                "sample_id": f"{global_index:04d}",
                "action_type": class_dir.name,
                "ground_truth_label": gt_label,
                "ground_truth_name": gt_name,
                "filename": src.name,
                "video_path": str(src),
                "seed": SEED,
                "sample_index_in_class": class_sample_index,
            })
            global_index += 1

        print(f"[OK] {class_dir.name}: {sample_count}/{len(videos)} selected")

    sample_csv = SAMPLES_DIR / f"sample_{N_PER_CLASS}_seed{SEED}.csv"
    with sample_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print("=" * 60)
    print(f"Done. Manifest saved to: {sample_csv}")
    print(f"Total selected videos: {len(rows)}")
    print("No video files were copied.")


if __name__ == "__main__":
    main()
