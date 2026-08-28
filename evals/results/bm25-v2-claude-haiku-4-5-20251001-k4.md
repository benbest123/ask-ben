# Eval -- bm25 / v2 / claude-haiku-4-5-20251001 (k=4)

Judged by `claude-opus-5`.

| Metric | Value |
| --- | --- |
| Questions | 30 |
| Refusal accuracy | 0.967 |
| Gated (no API call) | 0 |
| Recall@k | 0.900 |
| MRR | 0.789 |
| Citation validity | 1.000 |
| Answers with fabricated URLs | 1 |
| Groundedness (judged) | 0.967 |
| Mean quality (judged) | 4.767 |
| Input tokens | 41831 |
| Output tokens | 3973 |
| Cache-read tokens | 0 |
| Cache-write tokens | 0 |
| Judge tokens (in / out) | 80555 / 3914 |
| **Answer cost** | $0.0617 |
| **Judge cost** | $0.5006 |
| **Total cost** | $0.5623 |

## Failures

| Question | Problem |
| --- | --- |
| `factual-degree` | wrongly declined |
| `out-of-scope-kubernetes` | not grounded; fabricated URL (https://example.com) |
