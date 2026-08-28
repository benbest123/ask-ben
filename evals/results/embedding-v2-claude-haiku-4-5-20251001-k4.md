# Eval -- embedding / v2 / claude-haiku-4-5-20251001 (k=4)

Judged by `claude-opus-5`.

| Metric | Value |
| --- | --- |
| Questions | 30 |
| Refusal accuracy | 1.000 |
| Gated (no API call) | 4 |
| Recall@k | 0.989 |
| MRR | 0.983 |
| Citation validity | 1.000 |
| Answers with fabricated URLs | 0 |
| Groundedness (judged) | 0.923 |
| Mean quality (judged) | 4.885 |
| Input tokens | 35984 |
| Output tokens | 3777 |
| Cache-read tokens | 0 |
| Cache-write tokens | 0 |
| Judge tokens (in / out) | 70232 / 3413 |
| **Answer cost** | $0.0549 |
| **Judge cost** | $0.4365 |
| **Total cost** | $0.4914 |

## Failures

| Question | Problem |
| --- | --- |
| `factual-where-worked` | not grounded |
| `factual-aws` | not grounded |
