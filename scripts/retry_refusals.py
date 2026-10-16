"""Re-send every prompt that was refused, to test whether the refusal is reproducible.

    python scripts/retry_refusals.py --attempts 2

Identical prompt, identical parameters, fresh context. Original records are never overwritten;
each repeat is written to outputs/<model>/retries/<task>_attempt<N>.json. A refusal that holds
across attempts is deterministic for this prompt; one that does not is stochastic, and that
distinction matters for anyone acting on the result.
"""

import argparse
import datetime
import json
import os
from pathlib import Path

import anthropic
from confidence import parse_confidence
from run_models import EFFORT, SYSTEM, build_message

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempts", type=int, default=2)
    args = ap.parse_args()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY first.")

    tasks = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (ROOT / "tasks").glob("T*.json")}
    client = anthropic.Anthropic()

    refused = [json.loads(p.read_text(encoding="utf-8"))
               for p in sorted((ROOT / "outputs").glob("*/T*.json"))
               if json.loads(p.read_text(encoding="utf-8"))["refused"]]
    print(f"{len(refused)} refused responses to retry, {args.attempts} attempts each\n")

    for rec in refused:
        model, tid = rec["model"], rec["task_id"]
        out_dir = ROOT / "outputs" / model / "retries"
        out_dir.mkdir(parents=True, exist_ok=True)
        for attempt in range(1, args.attempts + 1):
            path = out_dir / f"{tid}_attempt{attempt}.json"
            if path.exists():
                continue
            try:
                with client.messages.stream(
                    model=model, max_tokens=32000, system=SYSTEM,
                    messages=[{"role": "user", "content": build_message(tasks[tid])}],
                    output_config={"effort": EFFORT},
                ) as stream:
                    msg = stream.get_final_message()
            except anthropic.APIStatusError as e:
                print(f"{model} {tid} attempt {attempt}: API error {e.status_code}")
                continue
            text = "".join(b.text for b in msg.content if b.type == "text")
            conf, _ = parse_confidence(text)
            out = {
                "task_id": tid, "model": model, "attempt": attempt, "served_by": msg.model,
                "effort": EFFORT, "date": datetime.date.today().isoformat(),
                "stop_reason": msg.stop_reason, "refused": msg.stop_reason == "refusal",
                "refusal_category": getattr(msg.stop_details, "category", None)
                                    if msg.stop_reason == "refusal" and msg.stop_details else None,
                "confidence": conf, "words": len(text.split()),
                "output_tokens": msg.usage.output_tokens, "output": text,
            }
            path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"{model} {tid} attempt {attempt}: "
                  + (f"REFUSED ({out['refusal_category']})" if out["refused"] else f"answered, {out['words']} words"))


if __name__ == "__main__":
    main()
