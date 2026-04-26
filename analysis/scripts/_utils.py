#!/usr/bin/env python3
"""Shared utilities for PhoTone analysis scripts.

How to use:
    Import helpers from this module inside scripts under analysis/scripts.

Notes:
    - Input CSV is expected at analysis/results/results.csv by default.
    - All scripts should write outputs under analysis/results and plots under
      analysis/results/plots.
"""

from __future__ import annotations

import csv
import math
import os
from collections import defaultdict
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np

FILTERS = [
    "filter-lark",
    "filter-sutro",
    "filter-hudson",
    "filter-1977",
    "filter-lofi",
    "filter-gingham",
    "filter-juno",
    "filter-inkwell",
    "filter-moon",
    "filter-clarendon",
]

STAGES = ["valence", "arousal"]


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def load_rows(csv_path: str) -> List[dict]:
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            normalized = {}
            for key, value in row.items():
                clean_key = (key or "").replace("\ufeff", "").strip()
                clean_value = value.strip() if isinstance(value, str) else value
                normalized[clean_key] = clean_value
            rows.append(normalized)
        return rows


def canonical_pair(a: str, b: str) -> Tuple[str, str]:
    return tuple(sorted((a, b)))


def get_loser(row: dict) -> str:
    selected = row["selected_filter"]
    left = row["filter_left"]
    right = row["filter_right"]
    if selected == left:
        return right
    if selected == right:
        return left
    raise ValueError(
        f"selected_filter {selected!r} is not in pair ({left!r}, {right!r})"
    )


def to_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def pearson(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return float("nan")
    mx = float(np.mean(x))
    my = float(np.mean(y))
    num = sum((a - mx) * (b - my) for a, b in zip(x, y))
    denx = math.sqrt(sum((a - mx) ** 2 for a in x))
    deny = math.sqrt(sum((b - my) ** 2 for b in y))
    if denx == 0 or deny == 0:
        return float("nan")
    return num / (denx * deny)


def rankdata(values: Sequence[float]) -> List[float]:
    indexed = sorted(enumerate(values), key=lambda x: x[1])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def spearman(x: Sequence[float], y: Sequence[float]) -> float:
    return pearson(rankdata(x), rankdata(y))


def bradley_terry_scores(
    winners: Iterable[Tuple[str, str]],
    filters: Sequence[str],
    max_iter: int = 500,
    tol: float = 1e-9,
) -> Dict[str, float]:
    """Estimate Bradley-Terry abilities using MM updates.

    Args:
        winners: Iterable of (winner, loser) tuples.
        filters: List of filter names to include in the model.

    Returns:
        Dict[filter] -> log-ability score (centered to mean 0).
    """
    filt = list(filters)
    idx = {name: i for i, name in enumerate(filt)}
    n = len(filt)

    win_counts = [0.0] * n
    comp_counts = [[0.0] * n for _ in range(n)]

    for winner, loser in winners:
        if winner not in idx or loser not in idx or winner == loser:
            continue
        i = idx[winner]
        j = idx[loser]
        win_counts[i] += 1.0
        comp_counts[i][j] += 1.0
        comp_counts[j][i] += 1.0

    # Add a tiny prior to avoid disconnected or zero-win instability.
    ability = [1.0] * n
    for _ in range(max_iter):
        new_ability = ability[:]
        for i in range(n):
            denom = 0.0
            for j in range(n):
                nij = comp_counts[i][j]
                if i != j and nij > 0:
                    denom += nij / (ability[i] + ability[j])
            numer = win_counts[i] + 1e-6
            if denom > 0:
                new_ability[i] = numer / denom
            else:
                new_ability[i] = ability[i]

        geom = math.exp(sum(math.log(max(v, 1e-12)) for v in new_ability) / n)
        new_ability = [max(v / geom, 1e-12) for v in new_ability]

        delta = max(abs(new_ability[i] - ability[i]) for i in range(n))
        ability = new_ability
        if delta < tol:
            break

    logs = [math.log(v) for v in ability]
    mu = float(np.mean(logs))
    logs = [v - mu for v in logs]
    return {filt[i]: logs[i] for i in range(n)}


def stage_rows(rows: List[dict], stage_name: str) -> List[dict]:
    return [r for r in rows if r.get("stage_name") == stage_name]


def infer_selected_side(row: dict) -> str:
    selected = row["selected_filter"]
    if selected == row["filter_left"]:
        return "left"
    if selected == row["filter_right"]:
        return "right"
    return "unknown"


def write_text(path: str, text: str) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def summarize_rt(values: Sequence[int]) -> Dict[str, float]:
    vals = [v for v in values if v >= 0]
    if not vals:
        return {"n": 0, "mean": float("nan"), "median": float("nan")}
    return {
        "n": len(vals),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
    }


def winners_from_rows(rows: Iterable[dict]) -> List[Tuple[str, str]]:
    pairs = []
    for row in rows:
        winner = row["selected_filter"]
        loser = get_loser(row)
        pairs.append((winner, loser))
    return pairs
