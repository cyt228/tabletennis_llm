from __future__ import annotations

from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["代碼", "類別", "具體動作描述", "主要判斷特徵"]


def load_action_guide(action_guide_path: str | Path) -> str:
    path = Path(action_guide_path)

    if not path.exists():
        raise FileNotFoundError(f"Action guide file not found: {path}")

    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    elif path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    else:
        raise ValueError(f"Unsupported action guide format: {path.suffix}")

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in action guide: {missing_cols}")

    df = df[REQUIRED_COLUMNS].copy()
    df = df.sort_values("代碼")

    guide_blocks = []

    for _, row in df.iterrows():
        code = int(row["代碼"])
        label = str(row["類別"]).strip()
        description = str(row["具體動作描述"]).strip()
        features = str(row["主要判斷特徵"]).strip()

        guide_blocks.append(
            f"[{code}] {label}\n"
            f"動作描述：{description}\n"
            f"主要判斷特徵：{features}"
        )

    return "\n\n".join(guide_blocks)