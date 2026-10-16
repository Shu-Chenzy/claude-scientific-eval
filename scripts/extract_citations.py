"""List every literature reference, identifier or outside dataset a response mentions, for manual F01 checks.

    python scripts/extract_citations.py --model claude-opus-5-5

Writes outputs/<model>/citations_to_verify.csv. This only finds candidates; whether each one
is real and says what the response claims is for the reviewer to decide.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "author_year": r"\b[A-Z][A-Za-z\-]+(?: and [A-Z][A-Za-z\-]+| et al\.?),? \(?(?:19|20)\d{2}\)?",
    "pmid": r"\bPMID:?\s*\d{6,9}\b",
    "doi": r"\b10\.\d{4,9}/[^\s,;)]+",
    "geo_or_trial": r"\b(?:GSE\d{3,7}|NCT\d{8})\b",
    "journal_year": r"\b(?:Nature|Science|Cell|Cancer Res(?:earch)?|Cancer Cell|Cancer Discov(?:ery)?|PNAS|"
                    r"N Engl J Med|NEJM|Lancet|JCO|J Clin Oncol|Clin Cancer Res|Nat Med|Eur Urol)\b[^.\n]{0,30}\b(?:19|20)\d{2}\b",
    "named_dataset": r"\b(?:TCGA|DepMap|CCLE|GTEx|Human Protein Atlas|HPA|cBioPortal|SU2C|WCDT|MSKCC|Taylor)\b",
}
IN_PACKET = {"GSE35988", "SU2C", "cBioPortal"}  # already in the input packet; listed but marked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-opus-5-5")
    args = parser.parse_args()
    out_dir = ROOT / "outputs" / args.model
    rows = []
    for p in sorted(out_dir.glob("T*.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        text = rec["output"]
        for kind, pat in PATTERNS.items():
            for m in re.finditer(pat, text):
                start, end = max(0, m.start() - 80), min(len(text), m.end() + 80)
                rows.append({
                    "task_id": rec["task_id"], "kind": kind, "match": m.group(0),
                    "in_input_packet": any(k in m.group(0) for k in IN_PACKET),
                    "context": " ".join(text[start:end].split()),
                    "verified_real": "", "supports_claim": "",
                })
    df = pd.DataFrame(rows).drop_duplicates(["task_id", "match"])
    path = out_dir / "citations_to_verify.csv"
    df.to_csv(path, index=False)
    print(f"{len(df)} references to check -> {path}")
    if len(df):
        print(df.groupby("kind").size().to_string())


if __name__ == "__main__":
    main()
