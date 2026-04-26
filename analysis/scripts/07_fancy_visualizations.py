#!/usr/bin/env python3
"""Publication-quality visualizations for PhoTone analysis.

How to execute:
    python analysis/scripts/07_fancy_visualizations.py \
        --input analysis/results/results.csv \
        --outdir analysis/results \
        --topn 8 \
        --boots 300

What this script does:
    - Builds a valence-arousal map with bootstrap uncertainty.
    - Builds ordered pairwise win-probability heatmaps by stage.
    - Builds filter ranking plots with bootstrap confidence intervals.
    - Builds agreement histograms and participant alignment distributions.
    - Builds small-multiple participant VA maps (top-N most complete sessions).
    - Builds reaction-time vs decision-difficulty scatter plots.
    - Builds image-level robustness strip plots and left/right bias checks.
    - Writes concise conclusions for these publication-style visuals.

Outputs:
    - CSV: analysis/results/fancy_visual_summary.csv
    - Plots: analysis/results/plots/fancy_*.png
    - Conclusion: analysis/results/conclusions/07_fancy_visualizations.md
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
import random

import matplotlib.pyplot as plt
import numpy as np

from _utils import (
    FILTERS,
    STAGES,
    bradley_terry_scores,
    canonical_pair,
    infer_selected_side,
    load_rows,
    spearman,
    stage_rows,
    to_int,
    winners_from_rows,
    write_text,
)


def set_style() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#fbfbfc",
            "axes.edgecolor": "#2c3e50",
            "axes.labelcolor": "#1f2d3d",
            "axes.titleweight": "bold",
            "axes.titlepad": 10,
            "xtick.color": "#1f2d3d",
            "ytick.color": "#1f2d3d",
            "grid.color": "#d7dde5",
            "font.size": 10,
            "savefig.transparent": False,
        }
    )


def save_figure(path: str, dpi: int = 300) -> None:
    """Save publication-ready raster and vector versions.

    If path ends with .png, this also emits a matching .pdf file.
    """
    # plt.savefig(path, dpi=dpi, bbox_inches="tight")
    if path.lower().endswith(".png"):
        pdf_path = path[:-4] + ".pdf"
        plt.savefig(pdf_path, dpi=dpi, bbox_inches="tight")


def build_subject_id_map(rows):
    """Assign stable subject_id values (starting from 1) by first appearance."""
    mapping = {}
    next_id = 1
    for r in rows:
        sid = r.get("session_id")
        if not sid:
            continue
        if sid not in mapping:
            mapping[sid] = next_id
            next_id += 1
    return mapping


def subject_label(session_id, subject_map):
    sid_num = subject_map.get(session_id)
    if sid_num is None:
        return "subject_unknown"
    return f"subject_{sid_num}"


def pairwise_winrate_matrix(rows, filters):
    idx = {f: i for i, f in enumerate(filters)}
    wins = np.zeros((len(filters), len(filters)), dtype=float)
    comps = np.zeros((len(filters), len(filters)), dtype=float)

    for r in rows:
        left = r["filter_left"]
        right = r["filter_right"]
        selected = r["selected_filter"]

        if left not in idx or right not in idx or left == right:
            continue

        i = idx[left]
        j = idx[right]
        comps[i, j] += 1
        comps[j, i] += 1

        if selected == left:
            wins[i, j] += 1
        elif selected == right:
            wins[j, i] += 1

    matrix = np.full((len(filters), len(filters)), np.nan, dtype=float)
    for i in range(len(filters)):
        for j in range(len(filters)):
            if i == j:
                continue
            if comps[i, j] > 0:
                matrix[i, j] = wins[i, j] / comps[i, j]

    return matrix


def plot_matrix(matrix, filters, title, out_path, vmin=0.0, vmax=1.0, cmap="viridis"):
    plt.figure(figsize=(8, 7))
    im = plt.imshow(matrix, vmin=vmin, vmax=vmax, cmap=cmap, interpolation="nearest")
    plt.xticks(range(len(filters)), [f.replace("filter-", "") for f in filters], rotation=45, ha="right")
    plt.yticks(range(len(filters)), [f.replace("filter-", "") for f in filters])
    plt.title(title)
    plt.colorbar(im, fraction=0.046, pad=0.04)
    plt.tight_layout()
    save_figure(out_path, dpi=220)
    plt.close()


def bootstrap_stage_scores(rows, filters, stage_name, boots=300, seed=42):
    rng = random.Random(seed)
    srows = stage_rows(rows, stage_name)
    by_session = defaultdict(list)
    for r in srows:
        by_session[r["session_id"]].append(r)

    sessions = list(by_session.keys())
    if not sessions:
        base = {f: float("nan") for f in filters}
        return base, {f: (float("nan"), float("nan")) for f in filters}, np.empty((0, len(filters)))

    base = bradley_terry_scores(winners_from_rows(srows), filters)
    boot_scores = []
    for _ in range(boots):
        sampled_sessions = [sessions[rng.randrange(len(sessions))] for _ in range(len(sessions))]
        sampled_rows = [r for sid in sampled_sessions for r in by_session[sid]]
        sc = bradley_terry_scores(winners_from_rows(sampled_rows), filters)
        boot_scores.append([sc[f] for f in filters])

    arr = np.array(boot_scores, dtype=float)
    ci = {}
    for i, f in enumerate(filters):
        lo = float(np.percentile(arr[:, i], 2.5))
        hi = float(np.percentile(arr[:, i], 97.5))
        ci[f] = (lo, hi)
    return base, ci, arr


def ordered_filters_by_score(score_map):
    return [k for k, _ in sorted(score_map.items(), key=lambda kv: kv[1], reverse=True)]


def plot_ranking_with_ci(stage_name, score_map, ci_map, out_path):
    ordered = ordered_filters_by_score(score_map)
    vals = np.array([score_map[f] for f in ordered], dtype=float)
    lo = np.array([ci_map[f][0] for f in ordered], dtype=float)
    hi = np.array([ci_map[f][1] for f in ordered], dtype=float)
    xerr = np.vstack([vals - lo, hi - vals])

    plt.figure(figsize=(9, 6))
    y = np.arange(len(ordered))
    plt.barh(y, vals, color="#2a9d8f", alpha=0.85)
    plt.errorbar(vals, y, xerr=xerr, fmt="none", ecolor="#264653", elinewidth=1.2, capsize=3)
    plt.yticks(y, [f.replace("filter-", "") for f in ordered])
    plt.axvline(0.0, linestyle="--", color="#7f8c8d", linewidth=1)
    plt.xlabel("Bradley-Terry score")
    plt.title(f"Filter ranking with 95% bootstrap CI ({stage_name})")
    plt.gca().invert_yaxis()
    plt.tight_layout()
    save_figure(out_path, dpi=240)
    plt.close()


def plot_va_map(val_scores, aro_scores, val_ci, aro_ci, out_path):
    names = list(val_scores.keys())
    xv = np.array([val_scores[f] for f in names], dtype=float)
    yv = np.array([aro_scores[f] for f in names], dtype=float)
    xlo = np.array([val_ci[f][0] for f in names], dtype=float)
    xhi = np.array([val_ci[f][1] for f in names], dtype=float)
    ylo = np.array([aro_ci[f][0] for f in names], dtype=float)
    yhi = np.array([aro_ci[f][1] for f in names], dtype=float)

    plt.figure(figsize=(8.5, 7.2))
    plt.scatter(xv, yv, s=90, color="#e76f51", edgecolor="white", linewidth=0.8, zorder=3)
    for i in range(len(names)):
        plt.plot([xlo[i], xhi[i]], [yv[i], yv[i]], color="#f4a261", alpha=0.8, linewidth=1.4)
        plt.plot([xv[i], xv[i]], [ylo[i], yhi[i]], color="#2a9d8f", alpha=0.8, linewidth=1.4)
        plt.text(xv[i] + 0.02, yv[i] + 0.02, names[i].replace("filter-", ""), fontsize=9)

    plt.axvline(0.0, linestyle="--", color="#7f8c8d", linewidth=1)
    plt.axhline(0.0, linestyle="--", color="#7f8c8d", linewidth=1)
    plt.xlabel("Valence score")
    plt.ylabel("Arousal score")
    plt.title("Valence-Arousal filter map with bootstrap uncertainty")
    plt.tight_layout()
    save_figure(out_path, dpi=260)
    plt.close()


def plot_small_multiples_va(
    rows_by_session,
    filters,
    val_global,
    aro_global,
    subject_map,
    out_path,
):
    sessions = list(rows_by_session.keys())
    n = len(sessions)
    if n == 0:
        return

    cols = 4
    rows = int(np.ceil(n / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(5.2 * cols, 4.8 * rows), squeeze=False, constrained_layout=True)

    # Compute a shared symmetric axis limit so (0, 0) is centered in every subplot.
    all_vals = []
    for sid in sessions:
        srows = rows_by_session[sid]
        sval = bradley_terry_scores(winners_from_rows(stage_rows(srows, "valence")), filters)
        saro = bradley_terry_scores(winners_from_rows(stage_rows(srows, "arousal")), filters)
        all_vals.extend([sval[f] for f in filters])
        all_vals.extend([saro[f] for f in filters])
    max_abs = max([abs(v) for v in all_vals], default=1.0)
    axis_lim = max(0.6, max_abs * 1.18)

    for ax in axes.flatten():
        ax.axis("off")

    for ax, sid in zip(axes.flatten(), sessions):
        ax.axis("on")
        srows = rows_by_session[sid]
        sval = bradley_terry_scores(winners_from_rows(stage_rows(srows, "valence")), filters)
        saro = bradley_terry_scores(winners_from_rows(stage_rows(srows, "arousal")), filters)
        xv = np.array([sval[f] for f in filters], dtype=float)
        yv = np.array([saro[f] for f in filters], dtype=float)
        colors = np.array([abs((sval[f] - val_global[f]) + (saro[f] - aro_global[f])) for f in filters])

        ax.scatter(
            xv,
            yv,
            s=95,
            c=colors,
            cmap="plasma",
            vmin=0,
            vmax=max(float(np.max(colors)), 0.1),
            edgecolors="white",
            linewidths=0.8,
            alpha=0.95,
        )
        ax.axvline(0.0, linestyle="-", linewidth=1.9, color="#4a6274")
        ax.axhline(0.0, linestyle="-", linewidth=1.9, color="#4a6274")

        # Keep subject labels but avoid subplot titles per request.
        ax.text(
            0.03,
            0.97,
            subject_label(sid, subject_map),
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=13,
            fontweight="bold",
            color="#1f2d3d",
        )

        ax.set_xlim(-axis_lim, axis_lim)
        ax.set_ylim(-axis_lim, axis_lim)
        ax.set_aspect("equal", adjustable="box")

        # Frame each subplot.
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.8)
            spine.set_color("#2c3e50")

        # Keep center ticks for orientation and enlarge text.
        ax.set_xticks([-axis_lim, 0.0, axis_lim])
        ax.set_yticks([-axis_lim, 0.0, axis_lim])
        ax.set_xticklabels(["", "0", ""], fontsize=11)
        ax.set_yticklabels(["", "0", ""], fontsize=11)
        ax.tick_params(length=0)

    save_figure(out_path, dpi=220)
    plt.close(fig)


def participant_alignment(rows, filters, stage_name):
    srows = stage_rows(rows, stage_name)
    global_scores = bradley_terry_scores(winners_from_rows(srows), filters)

    by_session = defaultdict(list)
    for r in srows:
        by_session[r["session_id"]].append(r)

    out = []
    for sid, sr in by_session.items():
        if len(sr) < 20:
            continue
        s_score = bradley_terry_scores(winners_from_rows(sr), filters)
        x = [global_scores[f] for f in filters]
        y = [s_score[f] for f in filters]
        out.append((sid, float(spearman(x, y)), len(sr)))
    return out


def agreement_values(rows, stage_name):
    srows = stage_rows(rows, stage_name)
    pair_choices = defaultdict(list)
    for r in srows:
        a, b = canonical_pair(r["filter_left"], r["filter_right"])
        if r["selected_filter"] in (a, b):
            pair_choices[(a, b)].append(r["selected_filter"])

    agreements = []
    for _, choices in pair_choices.items():
        if not choices:
            continue
        c = defaultdict(int)
        for ch in choices:
            c[ch] += 1
        mx = max(c.values())
        agreements.append(mx / len(choices))
    return agreements


def decision_difficulty_plot(rows, stage_name, score_map, out_path):
    srows = stage_rows(rows, stage_name)
    xs = []
    ys = []
    for r in srows:
        left = r["filter_left"]
        right = r["filter_right"]
        if left not in score_map or right not in score_map:
            continue
        diff = abs(score_map[left] - score_map[right])
        rt = to_int(r.get("reaction_time_ms", "0"), 0)
        if rt <= 0:
            continue
        xs.append(diff)
        ys.append(rt)

    if not xs:
        return

    xs_arr = np.array(xs, dtype=float)
    ys_arr = np.array(ys, dtype=float)
    corr = np.corrcoef(xs_arr, ys_arr)[0, 1] if len(xs_arr) > 1 else float("nan")

    plt.figure(figsize=(8, 5))
    plt.scatter(xs_arr, ys_arr, s=18, alpha=0.45, color="#264653", edgecolors="none")
    if len(xs_arr) > 1:
        coef = np.polyfit(xs_arr, ys_arr, 1)
        xline = np.linspace(float(np.min(xs_arr)), float(np.max(xs_arr)), 100)
        yline = coef[0] * xline + coef[1]
        plt.plot(xline, yline, color="#e76f51", linewidth=2)
    plt.xlabel("Decision difficulty |score_left - score_right|")
    plt.ylabel("Reaction time (ms)")
    plt.title(f"RT vs decision difficulty ({stage_name}), r={corr:.3f}")
    plt.tight_layout()
    save_figure(out_path, dpi=220)
    plt.close()


def left_right_bias_plot(rows, out_path):
    side_counts = defaultdict(int)
    for r in rows:
        side = infer_selected_side(r)
        if side in ("left", "right"):
            side_counts[side] += 1

    left = side_counts["left"]
    right = side_counts["right"]
    total = left + right
    if total == 0:
        return left, right, float("nan")

    plt.figure(figsize=(5.2, 4.4))
    plt.bar(["left", "right"], [left, right], color=["#457b9d", "#e63946"], alpha=0.88)
    plt.title("Left vs right chosen-side counts")
    plt.ylabel("Count")
    plt.tight_layout()
    save_figure(out_path, dpi=220)
    plt.close()

    return left, right, left / total


def image_robustness_plot(rows, score_map, stage_name, out_path):
    srows = stage_rows(rows, stage_name)
    by_img = defaultdict(list)
    for r in srows:
        by_img[r["img_id"]].append(r)

    vals = []
    labels = []
    for img, ir in sorted(by_img.items()):
        if len(ir) < 8:
            continue
        img_sc = bradley_terry_scores(winners_from_rows(ir), FILTERS)
        x = [score_map[f] for f in FILTERS]
        y = [img_sc[f] for f in FILTERS]
        vals.append(float(spearman(x, y)))
        labels.append(img)

    if not vals:
        return float("nan")

    x_pos = np.arange(len(vals))
    plt.figure(figsize=(max(8, 0.45 * len(vals)), 4.5))
    plt.scatter(x_pos, vals, s=36, color="#6a4c93")
    plt.axhline(float(np.mean(vals)), linestyle="--", color="#2a9d8f", linewidth=1.6)
    plt.xticks(x_pos, labels, rotation=75, ha="right", fontsize=8)
    plt.ylabel("Spearman(image ranking vs stage consensus)")
    plt.title(f"Image-level robustness ({stage_name})")
    plt.tight_layout()
    save_figure(out_path, dpi=220)
    plt.close()

    return float(np.mean(vals))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="analysis/results/results.csv")
    parser.add_argument("--outdir", default="analysis/results")
    parser.add_argument(
        "--topn",
        type=int,
        default=8,
        help="Number of most-complete participants to include in small-multiple individual VA maps.",
    )
    parser.add_argument("--boots", type=int, default=300)
    args = parser.parse_args()

    set_style()

    rows = load_rows(args.input)
    subject_map = build_subject_id_map(rows)
    plot_dir = os.path.join(args.outdir, "plots")
    concl_dir = os.path.join(args.outdir, "conclusions")
    out_csv = os.path.join(args.outdir, "fancy_visual_summary.csv")
    os.makedirs(plot_dir, exist_ok=True)
    os.makedirs(concl_dir, exist_ok=True)

    summary_records = []
    conclusion_lines = ["# Conclusion: Fancy Visualizations", ""]

    val_scores, val_ci, _ = bootstrap_stage_scores(rows, FILTERS, "valence", boots=args.boots, seed=11)
    aro_scores, aro_ci, _ = bootstrap_stage_scores(rows, FILTERS, "arousal", boots=args.boots, seed=29)

    plot_va_map(
        val_scores,
        aro_scores,
        val_ci,
        aro_ci,
        os.path.join(plot_dir, "fancy_va_map.png"),
    )

    # Ranking with CI (publication figure).
    plot_ranking_with_ci(
        "valence",
        val_scores,
        val_ci,
        os.path.join(plot_dir, "fancy_ranking_ci_valence.png"),
    )
    plot_ranking_with_ci(
        "arousal",
        aro_scores,
        aro_ci,
        os.path.join(plot_dir, "fancy_ranking_ci_arousal.png"),
    )

    # Small multiples use top complete sessions with both stages.
    by_session_all = defaultdict(list)
    for r in rows:
        by_session_all[r["session_id"]].append(r)
    ranked_sessions = sorted(by_session_all.items(), key=lambda kv: len(kv[1]), reverse=True)
    top_sessions = {sid: rr for sid, rr in ranked_sessions[: max(1, args.topn)]}
    plot_small_multiples_va(
        top_sessions,
        FILTERS,
        val_scores,
        aro_scores,
        subject_map,
        os.path.join(plot_dir, "fancy_individual_va_small_multiples.png"),
    )

    for stage in STAGES:
        srows = stage_rows(rows, stage)

        global_scores = val_scores if stage == "valence" else aro_scores

        # Ordered pairwise matrix for clear structure gradients.
        ord_filters = ordered_filters_by_score(global_scores)
        global_matrix = pairwise_winrate_matrix(srows, FILTERS)
        ord_idx = [FILTERS.index(f) for f in ord_filters]
        ord_mat = global_matrix[np.ix_(ord_idx, ord_idx)]
        plot_matrix(
            ord_mat,
            ord_filters,
            f"Ordered pairwise win-probability matrix ({stage})",
            os.path.join(plot_dir, f"fancy_consensus_matrix_{stage}.png"),
        )

        # Agreement distribution.
        agrees = agreement_values(rows, stage)
        if agrees:
            plt.figure(figsize=(7, 4.6))
            plt.hist(agrees, bins=10, edgecolor="#1f2d3d", color="#8ecae6")
            plt.title(f"Pairwise agreement distribution ({stage})")
            plt.xlabel("Agreement ratio per pair")
            plt.ylabel("Count of filter pairs")
            plt.tight_layout()
            save_figure(os.path.join(plot_dir, f"fancy_agreement_hist_{stage}.png"), dpi=220)
            plt.close()

        # Alignment scores + deviation heatmap.
        align_scores = participant_alignment(rows, FILTERS, stage)

        if align_scores:
            align_scores.sort(key=lambda x: x[1], reverse=True)
            sids = [subject_label(x[0], subject_map) for x in align_scores]
            vals = [x[1] for x in align_scores]

            plt.figure(figsize=(10, max(4, 0.35 * len(sids))))
            plt.barh(sids, vals)
            plt.axvline(0.0, linestyle="--", linewidth=1)
            plt.gca().invert_yaxis()
            plt.xlabel("Spearman alignment to stage consensus")
            plt.title(f"Participant alignment ({stage})")
            plt.tight_layout()
            save_figure(os.path.join(plot_dir, f"fancy_alignment_bar_{stage}.png"), dpi=220)
            plt.close()

            # Build deviation map in this ordered set.
            dev_rows = []
            for sid, _, _ in align_scores:
                sid_rows = [r for r in srows if r["session_id"] == sid]
                sid_scores = bradley_terry_scores(winners_from_rows(sid_rows), FILTERS)
                dev_rows.append([sid_scores[f] - global_scores[f] for f in FILTERS])
            dev_arr = np.array(dev_rows, dtype=float)
            # Reorder heatmap rows by alignment rank for readability.
            dev_ordered = dev_arr
            row_labels = sids

            plt.figure(figsize=(10, max(4, 0.35 * len(row_labels))))
            vmax = float(np.nanmax(np.abs(dev_ordered))) if dev_ordered.size else 1.0
            vmax = max(vmax, 0.5)
            im = plt.imshow(dev_ordered, aspect="auto", cmap="coolwarm", vmin=-vmax, vmax=vmax)
            plt.yticks(range(len(row_labels)), row_labels)
            plt.xticks(range(len(FILTERS)), [f.replace("filter-", "") for f in FILTERS], rotation=45, ha="right")
            plt.title(f"Participant-filter deviation heatmap ({stage})")
            cbar = plt.colorbar(im, fraction=0.03, pad=0.02)
            cbar.ax.set_ylabel("Participant BT score - consensus BT score", rotation=90)
            plt.tight_layout()
            save_figure(
                os.path.join(plot_dir, f"fancy_alignment_deviation_heatmap_{stage}.png"),
                dpi=220,
            )
            plt.close()

            top = align_scores[0]
            bottom = align_scores[-1]
            avg = float(np.mean([x[1] for x in align_scores]))
            conclusion_lines.extend(
                [
                    f"## {stage.capitalize()}",
                    f"- Mean participant alignment (Spearman): {avg:.3f}",
                    f"- Most aligned participant: {subject_label(top[0], subject_map)} ({top[1]:.3f})",
                    f"- Least aligned participant: {subject_label(bottom[0], subject_map)} ({bottom[1]:.3f})",
                    f"- Sessions included in alignment: {len(align_scores)}",
                    "",
                ]
            )

            for sid, rho, n_trials in align_scores:
                summary_records.append(
                    {
                        "metric": "alignment_spearman",
                        "stage": stage,
                        "entity": subject_label(sid, subject_map),
                        "value": f"{rho:.6f}",
                        "n": n_trials,
                    }
                )

        # Decision difficulty vs RT.
        decision_difficulty_plot(
            rows,
            stage,
            global_scores,
            os.path.join(plot_dir, f"fancy_rt_vs_difficulty_{stage}.png"),
        )

        # Image-level robustness strip plot.
        img_mean = image_robustness_plot(
            rows,
            global_scores,
            stage,
            os.path.join(plot_dir, f"fancy_image_robustness_{stage}.png"),
        )
        summary_records.append(
            {
                "metric": "image_robustness_mean_spearman",
                "stage": stage,
                "entity": "all_images",
                "value": f"{img_mean:.6f}",
                "n": "",
            }
        )

    # Side-bias sanity plot over all rows.
    left, right, left_rate = left_right_bias_plot(
        rows,
        os.path.join(plot_dir, "fancy_left_right_bias.png"),
    )
    summary_records.append(
        {
            "metric": "left_choice_rate",
            "stage": "all",
            "entity": "all_sessions",
            "value": f"{left_rate:.6f}",
            "n": left + right,
        }
    )

    conclusion_lines.extend(
        [
            "## Validity checks",
            f"- Left choices: {left}",
            f"- Right choices: {right}",
            f"- Left-choice rate: {left_rate:.3f}",
            "",
            "Main figure set now emphasizes structure (VA map + ordered matrices), uncertainty (bootstrap CI), participant heterogeneity (alignment + small multiples), and validity checks (image robustness + side bias).",
            "",
            "Redundancy note: this script consolidates the previously separate advanced visual ideas into one publication-oriented output set.",
        ]
    )

    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["metric", "stage", "entity", "value", "n"],
        )
        writer.writeheader()
        writer.writerows(summary_records)

    write_text(
        os.path.join(concl_dir, "07_fancy_visualizations.md"),
        "\n".join(conclusion_lines) + "\n",
    )

    print(f"Wrote {out_csv}")
    print(f"Wrote plots under {plot_dir}")
    print("Wrote conclusions: analysis/results/conclusions/07_fancy_visualizations.md")


if __name__ == "__main__":
    main()
