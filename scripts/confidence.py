"""Pull the stated confidence out of a response.

Responses write it in several shapes: "Confidence: 75%", "## 10. Confidence\n\n**75%**",
"...confidence is higher (~80%)". Returns (value, snippet) so the reviewer can check the
number against its context; value is None when no percentage follows the last heading.
"""

import re

PCT = re.compile(r"(?<![\d.])(\d{1,3})\s*(?:%|percent)")
HEADING = re.compile(r"(?mi)^#*\s*(?:10\s*[.)])?\s*Confidence")


def parse_confidence(text, window=400):
    # Candidate anchors, latest first. A later sentence often qualifies the number ("Confidence is
    # highest for C1..."), so take the latest anchor that actually has a percentage after it rather
    # than simply the last mention of the word.
    heads = [m.start() for m in HEADING.finditer(text)]
    heads += [m.start() for m in re.finditer(r"(?i)confidence", text)]
    if not heads:
        return None, ""
    for i in sorted(set(heads), reverse=True):
        m = PCT.search(text[i:i + window])
        if m:
            value = int(m.group(1))
            if 0 <= value <= 100:
                return value, " ".join(text[i:i + m.end() + 60].split())
    last = max(heads)
    return None, " ".join(text[last:last + 160].split())
