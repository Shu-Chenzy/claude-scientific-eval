"""Run every task against each model, in a fresh context, with identical prompts.

    python scripts/run_models.py
    python scripts/run_models.py --models claude-opus-5-5 --tasks T1

Server-side refusal fallbacks are deliberately NOT used. If a model declines, that is recorded as
a refusal rather than being answered by a different model, so refusal rate is comparable across
models. Outputs: outputs/<model>/<task_id>.json and .md.
"""

import argparse
import datetime
import json
import os
from pathlib import Path

import anthropic
from confidence import parse_confidence

ROOT = Path(__file__).resolve().parents[1]
MODELS = ["claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5"]
EFFORT = "high"

SYSTEM = (
    "You are assisting an experimental cancer biologist who will use your answer to decide what "
    "experiments to run next. Base your answer on the material provided. If you use knowledge that "
    "is not in the material, label it explicitly as outside knowledge. Use the numbered headings "
    "requested in the question, and end with a single confidence number from 0 to 100%."
)


def load_tasks(selected):
    tasks = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "tasks").glob("T*.json"))]
    return [t for t in tasks if not selected or t["task_id"] in selected]


def build_message(task):
    parts = [task["prompt"]]
    for rel in task["input_files"]:
        parts.append(f"\n\n--- Provided material: {Path(rel).name} ---\n" + (ROOT / rel).read_text(encoding="utf-8"))
    return "".join(parts)


def ask(client, model, task, fallback=False):
    # fallback=True is the separate, clearly-labelled arm: on a refusal the API re-runs the request
    # on another model inside the same call, so the answer may not come from `model`. served_by says
    # which model actually produced it.
    extra = ({"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} if fallback else {})
    stream_ctx = (client.beta.messages.stream if fallback else client.messages.stream)
    with stream_ctx(
        model=model,
        max_tokens=32000,
        system=SYSTEM,
        messages=[{"role": "user", "content": build_message(task)}],
        output_config={"effort": EFFORT},
        **extra,
    ) as stream:
        msg = stream.get_final_message()

    text = "".join(b.text for b in msg.content if b.type == "text")
    refused = msg.stop_reason == "refusal"
    conf, snippet = parse_confidence(text)
    return {
        "task_id": task["task_id"], "capability": task["capability"], "model": model,
        "served_by": msg.model, "effort": EFFORT, "date": datetime.date.today().isoformat(),
        "prompt_version": task["prompt_version"], "input_version": task["input_version"],
        "stop_reason": msg.stop_reason, "refused": refused,
        "refusal_category": getattr(msg.stop_details, "category", None) if refused and msg.stop_details else None,
        "confidence": conf, "confidence_snippet": snippet,
        "input_tokens": msg.usage.input_tokens, "output_tokens": msg.usage.output_tokens,
        "words": len(text.split()), "output": text,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=MODELS)
    ap.add_argument("--tasks", nargs="*")
    ap.add_argument("--fallback", action="store_true",
                    help="enable server-side refusal fallbacks; writes to outputs/<model>+fallback/")
    args = ap.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first.")

    client = anthropic.Anthropic()
    for model in args.models:
        out_dir = ROOT / "outputs" / (f"{model}+fallback" if args.fallback else model)
        out_dir.mkdir(parents=True, exist_ok=True)
        for task in load_tasks(args.tasks):
            path = out_dir / f"{task['task_id']}.json"
            if path.exists():
                continue
            try:
                rec = ask(client, model, task, fallback=args.fallback)
            except anthropic.AuthenticationError:
                raise SystemExit("API key missing or invalid.")
            except anthropic.BadRequestError as e:
                print(f"{model} {task['task_id']}: bad request, skipped ({e.message})")
                continue
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                print(f"{model} {task['task_id']}: {type(e).__name__}, stopping; re-run to resume")
                return
            path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
            path.with_suffix(".md").write_text(
                f"# {task['task_id']} {task['title']}\n\nmodel `{model}`, effort {EFFORT}, {rec['date']}, "
                f"stop `{rec['stop_reason']}`, confidence {rec['confidence']}, {rec['words']} words\n\n"
                f"## Prompt\n\n{task['prompt']}\n\n## Response\n\n{rec['output']}\n", encoding="utf-8")
            flag = "REFUSED" if rec["refused"] else f"conf={rec['confidence']}"
            served = "" if rec["served_by"] == model else f"  served_by={rec['served_by']}"
            print(f"{out_dir.name:<28} {task['task_id']}  {flag}  {rec['words']} words"
                  f"  {rec['output_tokens']} out-tok{served}")


if __name__ == "__main__":
    main()
