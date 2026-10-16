"""Re-read the stated confidence from saved responses, without calling the API again.

    python scripts/reparse_confidence.py

Models write the number in several shapes, so the parser is updated from time to time. This
re-applies it to every saved response and reports any that still have no number.
"""

import json
from pathlib import Path

from confidence import parse_confidence

ROOT = Path(__file__).resolve().parents[1]


def main():
    missing, n = [], 0
    for p in sorted((ROOT / "outputs").rglob("T*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if "output" not in rec:
            continue
        rec["confidence"], rec["confidence_snippet"] = parse_confidence(rec["output"])
        p.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
        n += 1
        if rec["confidence"] is None and rec["output"].strip():
            missing.append((rec["model"], rec["task_id"], rec["confidence_snippet"][:100]))

    print(f"reparsed {n} responses; {len(missing)} answered responses have no numeric confidence")
    for m, t, s in missing:
        print(f"  {m} {t}: {s}")


if __name__ == "__main__":
    main()
