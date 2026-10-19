"""Unblind completed scores and summarize the primary and fallback arms separately.

Primary responses are scored under the model that actually answered the prompt. If the requested
model refused and a fallback run was used to obtain a scoreable answer, that response is reported
separately and is never folded into the requested model's mean.
"""

import argparse
import shutil
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CORE = [
    "biological_correctness",
    "evidence_grounding",
    "causal_reasoning",
    "experimental_feasibility",
    "falsifiability",
    "uncertainty_calibration",
]
FCODES = [f"F{i:02d}" for i in range(1, 16)]
SHORT = {
    "claude-haiku-5-5": "Haiku 5.5",
    "claude-sonnet-5-5": "Sonnet 5.5",
    "claude-opus-5-5": "Opus 5.5",
    "claude-opus-5": "Opus 5 fallback",
}

plt.rcParams.update(
    {
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "font.size": 9,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def load_scores():
    csv_path = ROOT / "scoring" / "blind_scores.csv"
    xlsx_path = ROOT / "scoring" / "blind_scores.xlsx"
    if xlsx_path.exists() and (not csv_path.exists() or xlsx_path.stat().st_mtime > csv_path.stat().st_mtime):
        df = pd.read_excel(xlsx_path, sheet_name="scores")
        df.to_csv(csv_path, index=False)
    else:
        df = pd.read_csv(csv_path)

    key_path = ROOT / "private" / "blinding_key.csv"
    if not key_path.exists():
        key_path = ROOT / "results" / "blinding_key.csv"
    key = pd.read_csv(key_path)[["task_id", "label", "model", "arm", "served_by"]]

    df = df.merge(key, left_on=["task_id", "response"], right_on=["task_id", "label"], how="left")
    for col in CORE + FCODES + ["confidence", "words"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["mean_core"] = df[CORE].mean(axis=1)
    df["requested_model"] = df["model"]
    df["requested_short"] = df["requested_model"].map(SHORT)
    df["served_short"] = df["served_by"].map(SHORT).fillna(df["served_by"])
    df["is_primary"] = (df["arm"] == df["requested_model"]) & (df["served_by"] == df["requested_model"])
    return df


def summarize(df):
    scored = df.dropna(subset=["mean_core"]).copy()
    primary = scored[scored["is_primary"]].copy()
    fallback = scored[~scored["is_primary"]].copy()

    ref = pd.read_csv(ROOT / "results" / "refusals.csv")
    requested_order = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]

    rows = []
    for model in requested_order:
        sub = primary[primary.requested_model == model]
        refused = 0
        if "model" in ref.columns:
            labels = set(ref["model"].astype(str))
            key = SHORT[model] if SHORT[model] in labels else model
            refused = int(ref.loc[ref["model"] == key, "refused"].sum())
        rows.append(
            {
                "model": SHORT[model],
                "primary_answered": len(sub),
                "primary_refused": refused,
                "mean_core_answered": sub.mean_core.mean() if len(sub) else np.nan,
                "mean_words_answered": sub.words.mean() if len(sub) else np.nan,
                "mean_confidence_answered": sub.confidence.mean() if len(sub) else np.nan,
                "failure_flags_primary": sub[FCODES].sum().sum() if len(sub) else 0,
            }
        )
    primary_summary = pd.DataFrame(rows).set_index("model")

    counts = primary.groupby("task_id").requested_model.nunique()
    common_tasks = counts[counts == len(requested_order)].index.tolist()
    common = primary[primary.task_id.isin(common_tasks)]
    common_summary = (
        common.groupby("requested_short")
        .agg(n=("task_id", "size"), mean_core=("mean_core", "mean"), mean_words=("words", "mean"), mean_confidence=("confidence", "mean"))
        .reindex([SHORT[m] for m in requested_order])
    )

    if len(fallback):
        fallback_summary = (
            fallback.groupby(["requested_short", "served_short"])
            .agg(n=("task_id", "size"), mean_core=("mean_core", "mean"), mean_words=("words", "mean"), mean_confidence=("confidence", "mean"))
        )
    else:
        fallback_summary = pd.DataFrame()

    by_dim = primary.groupby("requested_short")[CORE].mean().reindex([SHORT[m] for m in requested_order])
    by_cap = primary.pivot_table(index="capability", columns="requested_short", values="mean_core").reindex(
        columns=[SHORT[m] for m in requested_order]
    )
    by_fail = primary.groupby("requested_short")[FCODES].sum().reindex([SHORT[m] for m in requested_order])
    by_fail = by_fail.loc[:, by_fail.sum() > 0]

    return scored, primary, fallback, primary_summary, common_tasks, common_summary, fallback_summary, by_dim, by_cap, by_fail


def write_outputs(primary_summary, common_tasks, common_summary, fallback_summary, by_dim, by_cap, by_fail):
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "figures").mkdir(exist_ok=True)
    primary_summary.round(2).to_csv(out / "model_summary.csv")
    common_summary.round(2).to_csv(out / "common_task_summary.csv")
    if not fallback_summary.empty:
        fallback_summary.round(2).to_csv(out / "fallback_summary.csv")
    by_dim.round(2).to_csv(out / "by_dimension.csv")
    by_cap.round(2).to_csv(out / "by_capability.csv")
    by_fail.to_csv(out / "failures_by_model.csv")
    (out / "common_tasks.txt").write_text("\n".join(common_tasks) + "\n", encoding="utf-8")


def make_figures(scored, primary, fallback, primary_summary, common_summary, by_cap):
    fig, axes = plt.subplots(1, 2, figsize=(8.6, 3.4))
    models = list(primary_summary.index)
    answered = primary_summary.primary_answered.values
    refused = primary_summary.primary_refused.values
    x = np.arange(len(models))
    axes[0].bar(x, answered, label="answered")
    axes[0].bar(x, refused, bottom=answered, label="refused")
    axes[0].set_xticks(x, models)
    axes[0].set_ylim(0, 6.5)
    axes[0].set_ylabel("tasks (of 6)")
    axes[0].set_title("Primary-arm completion")
    axes[0].legend(frameon=False, fontsize=8)

    vals = common_summary.mean_core.values
    axes[1].bar(np.arange(len(common_summary)), vals)
    axes[1].set_xticks(np.arange(len(common_summary)), common_summary.index)
    axes[1].set_ylim(1, 5.2)
    axes[1].set_ylabel("mean core score")
    axes[1].set_title("Common tasks only")
    for i, v in enumerate(vals):
        if pd.notna(v):
            axes[1].text(i, v + 0.06, f"{v:.2f}", ha="center", fontsize=8)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "01_overall_model_performance.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.8, 3.8))
    caps = list(by_cap.index)
    x = np.arange(len(caps))
    width = 0.24
    for i, model in enumerate(by_cap.columns):
        vals = by_cap[model].values
        ax.bar(x + (i - 1) * width, vals, width=width, label=model)
    ax.set_xticks(x, [c.replace(" and ", " &\n").replace(" ", "\n", 1) for c in caps], fontsize=6.5)
    ax.set_ylim(1, 5.2)
    ax.set_ylabel("mean core score")
    ax.set_title("Primary-arm scores by task capability")
    ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "02_by_capability.png", bbox_inches="tight")
    plt.close(fig)

    display = primary.copy()
    display["analysis_arm"] = display["requested_short"]
    if len(fallback):
        fb = fallback.copy()
        fb["analysis_arm"] = fb["served_short"]
        display = pd.concat([display, fb], ignore_index=True)
    fail = display.groupby("analysis_arm")[FCODES].sum()
    fail = fail.loc[:, fail.sum() > 0]
    fig, ax = plt.subplots(figsize=(8.8, 3.5))
    if fail.empty:
        ax.text(0.5, 0.5, "No failure codes assigned", ha="center", va="center")
        ax.axis("off")
    else:
        x = np.arange(fail.shape[1])
        width = 0.8 / max(1, len(fail.index))
        for i, arm in enumerate(fail.index):
            ax.bar(x - 0.4 + width / 2 + i * width, fail.loc[arm], width=width, label=arm)
        ax.set_xticks(x, fail.columns, fontsize=7)
        ax.set_ylabel("responses flagged")
        ax.set_title("Failure codes in scored responses")
        ax.legend(frameon=False, fontsize=7)
    fig.tight_layout()
    fig.savefig(ROOT / "results" / "figures" / "03_failure_modes.png", bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish-key", action="store_true")
    args = ap.parse_args()

    df = load_scores()
    (
        scored,
        primary,
        fallback,
        primary_summary,
        common_tasks,
        common_summary,
        fallback_summary,
        by_dim,
        by_cap,
        by_fail,
    ) = summarize(df)

    write_outputs(primary_summary, common_tasks, common_summary, fallback_summary, by_dim, by_cap, by_fail)
    make_figures(scored, primary, fallback, primary_summary, common_summary, by_cap)

    print("Primary-arm summary:\n", primary_summary.round(2).to_string())
    print("\nCommon tasks:", ", ".join(common_tasks) if common_tasks else "none")
    print("\nCommon-task comparison:\n", common_summary.round(2).to_string())
    if not fallback_summary.empty:
        print("\nFallback arm:\n", fallback_summary.round(2).to_string())

    all_scored = scored[["confidence", "words", "mean_core"]].dropna()
    if len(all_scored) > 3:
        print(
            f"\nConfidence vs score: Spearman rho = {all_scored.confidence.corr(all_scored.mean_core, method='spearman'):.2f}"
        )
        print(f"Length vs score:     Spearman rho = {all_scored.words.corr(all_scored.mean_core, method='spearman'):.2f}")

    if args.publish_key:
        private_key = ROOT / "private" / "blinding_key.csv"
        if private_key.exists():
            shutil.copy(private_key, ROOT / "results" / "blinding_key.csv")
            print("\nPublished blinding key to results/blinding_key.csv")


if __name__ == "__main__":
    main()
