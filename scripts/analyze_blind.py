"""Unblind the scores and produce the comparison tables and figures.

    python scripts/analyze_blind.py                # after scoring/blind_scores.xlsx is filled in
    python scripts/analyze_blind.py --publish-key  # also copy the mapping into results/ for the repo

Joins scoring/blind_scores.csv (or .xlsx if newer) to private/blinding_key.csv. Run this only once
scoring is finished: it reveals which response came from which model.
"""

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORE = ["biological_correctness", "evidence_grounding", "causal_reasoning",
        "experimental_feasibility", "falsifiability", "uncertainty_calibration"]
FCODES = [f"F{i:02d}" for i in range(1, 16)]
SHORT = {"claude-haiku-5-5": "Haiku 5.5", "claude-sonnet-5-5": "Sonnet 5.5", "claude-opus-5-5": "Opus 5.5"}
COLOR = {"Haiku 5.5": "#9e9e9e", "Sonnet 5.5": "#3b75af", "Opus 5.5": "#c0392b"}

plt.rcParams.update({"figure.dpi": 110, "savefig.dpi": 300, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False})


def load():
    csv, xlsx = ROOT / "scoring" / "blind_scores.csv", ROOT / "scoring" / "blind_scores.xlsx"
    if xlsx.exists() and (not csv.exists() or xlsx.stat().st_mtime > csv.stat().st_mtime):
        df = pd.read_excel(xlsx, sheet_name="scores")
        df.to_csv(csv, index=False)
    else:
        df = pd.read_csv(csv)
    key = pd.read_csv(ROOT / "private" / "blinding_key.csv")[["task_id", "label", "model"]]
    df = df.merge(key, left_on=["task_id", "response"], right_on=["task_id", "label"], how="left")
    df["model_short"] = df.model.map(SHORT)
    for c in CORE + FCODES + ["confidence", "words"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["mean_core"] = df[CORE].mean(axis=1)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish-key", action="store_true")
    args = ap.parse_args()
    df = load()

    scored = df.dropna(subset=["mean_core"])
    if scored.empty:
        raise SystemExit("No scores yet. Fill scoring/blind_scores.xlsx first.")
    if len(scored) < len(df):
        print(f"note: {len(df) - len(scored)} of {len(df)} responses are unscored and are left out\n")

    order = [m for m in SHORT.values() if m in set(scored.model_short)]
    (ROOT / "results" / "figures").mkdir(parents=True, exist_ok=True)

    overall = scored.groupby("model_short").agg(
        n=("task_id", "size"), mean_core=("mean_core", "mean"),
        mean_words=("words", "mean"), mean_confidence=("confidence", "mean")).reindex(order)
    overall["failure_flags"] = scored.groupby("model_short")[FCODES].sum().sum(axis=1).reindex(order)
    # refusals are a property of the model, not of a scored answer; they live in results/refusals.csv
    ref = pd.read_csv(ROOT / "results" / "refusals.csv")
    overall["refusals_primary_arm"] = ref.groupby("model").refused.sum().reindex(order).fillna(0).astype(int)
    by_dim = scored.groupby("model_short")[CORE].mean().reindex(order)
    by_cap = scored.pivot_table(index="capability", columns="model_short", values="mean_core").reindex(columns=order)
    by_fail = scored.groupby("model_short")[FCODES].sum().reindex(order)
    by_fail = by_fail.loc[:, by_fail.sum() > 0]

    overall.round(2).to_csv(ROOT / "results" / "model_summary.csv")
    by_dim.round(2).to_csv(ROOT / "results" / "by_dimension.csv")
    by_cap.round(2).to_csv(ROOT / "results" / "by_capability.csv")
    by_fail.to_csv(ROOT / "results" / "failures_by_model.csv")

    print("Overall:\n" + overall.round(2).to_string())
    print("\nBy dimension:\n" + by_dim.round(2).to_string())
    print("\nBy capability:\n" + by_cap.round(2).to_string())
    print("\nFailure codes fired:\n" + (by_fail.to_string() if not by_fail.empty else "  none"))

    # Figure 1: overall performance
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4))
    axes[0].bar(overall.index, overall.mean_core, color=[COLOR[m] for m in overall.index])
    axes[0].set_ylim(1, 5.2)
    axes[0].axhline(5, ls="--", lw=0.7, color="grey")
    axes[0].set_ylabel("mean core score (1-5)")
    axes[0].set_title("Overall performance")
    for i, v in enumerate(overall.mean_core):
        axes[0].text(i, v + 0.07, f"{v:.2f}", ha="center", fontsize=8)

    w = 0.26
    x = np.arange(len(CORE))
    for i, m in enumerate(order):
        axes[1].bar(x + (i - 1) * w, by_dim.loc[m], width=w, label=m, color=COLOR[m])
    axes[1].set_xticks(x, [c.replace("_", "\n") for c in CORE], fontsize=6)
    axes[1].set_ylim(1, 5.2)
    axes[1].set_title("By rubric dimension")
    axes[1].legend(frameon=False, fontsize=7)

    axes[2].scatter(scored.words, scored.mean_core, s=28,
                    c=[COLOR[m] for m in scored.model_short], alpha=0.85)
    axes[2].set_xlabel("answer length (words)")
    axes[2].set_ylabel("mean core score")
    axes[2].set_title("Does length buy quality?")
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "01_overall_model_performance.png", bbox_inches="tight")

    # Figure 2: capability profile
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    caps = list(by_cap.index)
    x = np.arange(len(caps))
    for i, m in enumerate(order):
        ax.bar(x + (i - 1) * w, by_cap[m], width=w, label=m, color=COLOR[m])
    ax.set_xticks(x, [c.replace(" and ", " &\n").replace(" ", "\n", 1) for c in caps], fontsize=6.5)
    ax.set_ylim(1, 5.2)
    ax.axhline(5, ls="--", lw=0.7, color="grey")
    ax.set_ylabel("mean core score")
    ax.set_title("Performance by scientific capability")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "02_by_capability.png", bbox_inches="tight")

    # Figure 3: failure modes
    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    if by_fail.empty:
        ax.text(0.5, 0.5, "No failure codes were assigned", ha="center", va="center", fontsize=11)
        ax.axis("off")
    else:
        names = {"F01": "hallucinated\nevidence", "F02": "unsupported\nmechanism", "F03": "correlation\nas causation",
                 "F04": "missing\nalternative", "F05": "missing\ncontrol", "F06": "infeasible\nexperiment",
                 "F07": "incorrect\nexperimental logic", "F08": "overconfident\nconclusion",
                 "F09": "missed\ncontradiction", "F10": "known idea\nas novel", "F11": "poor\nprioritization",
                 "F12": "ignored negative\nevidence", "F13": "unnecessary\nexperimentation",
                 "F14": "clinically\nunrealistic", "F15": "right answer,\nwrong reason"}
        x = np.arange(by_fail.shape[1])
        for i, m in enumerate(order):
            ax.bar(x + (i - 1) * w, by_fail.loc[m], width=w, label=m, color=COLOR[m])
        ax.set_xticks(x, [f"{c}\n{names.get(c, '')}" for c in by_fail.columns], fontsize=7)
        ax.set_yticks(range(0, int(by_fail.values.max()) + 2))
        ax.set_ylabel("responses with this failure")
        ax.set_title("Failure modes by model")
        ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "03_failure_modes.png", bbox_inches="tight")

    r = scored[["confidence", "mean_core"]].dropna()
    if len(r) > 3:
        print(f"\nConfidence vs score: Spearman rho = {r.confidence.corr(r.mean_core, method='spearman'):.2f} "
              f"(n = {len(r)}; score sd {scored.mean_core.std():.2f})")
    lw = scored[["words", "mean_core"]].dropna()
    if len(lw) > 3:
        print(f"Length vs score:     Spearman rho = {lw.words.corr(lw.mean_core, method='spearman'):.2f}")

    if args.publish_key:
        shutil.copy(ROOT / "private" / "blinding_key.csv", ROOT / "results" / "blinding_key.csv")
        print("\ncopied the mapping to results/blinding_key.csv for publication")

    print("\nwrote results/*.csv and 3 figures")


if __name__ == "__main__":
    main()
