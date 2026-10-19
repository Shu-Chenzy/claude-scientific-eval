"""Pull the stated confidence out of a response.

Responses write it in several shapes: "Confidence: 75%", "## 10. Confidence\n\n**75%**",
"...confidence is higher (~80%)". Returns (value, snippet) so the reviewer can check the
number against its context; value is None when no percentage follows the last heading.
"""

import re

PCT = re.compile(r"(?<![\d.])(\d{1,3})\s*(?:%|percent)")
# A real heading only: "## 10. Confidence", "**Confidence**", "10) Confidence". A sentence that
# merely begins with the word ("Confidence that X is correct...") is not an anchor — the number
# after such a clause is usually a contrast ("held below 70%", "more confident (~75%)"), not the
# answer. Take the FIRST percentage after the LAST real heading.
HEADING = re.compile(r"(?mi)^(?:#{1,6}\s*|\*{1,2}\s*)(?:10\s*[.)]\s*)?Confidence\b|^10\s*[.)]\s*Confidence\b")


def parse_confidence(text, window=400):
    heads = [m.start() for m in HEADING.finditer(text)]
    fallback = [m.start() for m in re.finditer(r"(?i)confidence", text)]
    for anchors in (heads, fallback):          # real headings first, bare mentions only if none
        for i in sorted(set(anchors), reverse=True):
            m = PCT.search(text[i:i + window])
            if m:
                value = int(m.group(1))
                if 0 <= value <= 100:
                    return value, " ".join(text[i:i + m.end() + 60].split())
            if anchors is heads:               # a heading was found: trust it, do not scan earlier
                break
    last = max(heads + fallback, default=None)
    return (None, "" if last is None else " ".join(text[last:last + 160].split()))
