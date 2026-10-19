# Refusal record

Primary-arm fallbacks were disabled so a refusal could not be silently replaced by another model.

| Task | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| T1 | answered | answered | answered |
| T2 | answered | answered | answered |
| T3 | answered | answered | refused |
| T4 | answered | answered | refused |
| T5 | answered | answered | refused |
| T6 | answered | answered | refused |

All four Opus 5.5 refusals had `stop_details.category = "bio"`. Each refused prompt was sent twice more under the same conditions; all four refused on all three attempts.

A separate fallback-enabled arm was then run so the refused tasks could still be inspected. In each case the API served the answer from `claude-opus-5`. These outputs are stored under `outputs/claude-opus-5-5+fallback/` and are treated as supplementary Opus 5 responses, not as Opus 5.5 results.
