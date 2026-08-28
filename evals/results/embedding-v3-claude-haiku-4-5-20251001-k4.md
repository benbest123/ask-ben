# Eval -- embedding / v3 / claude-haiku-4-5-20251001 (k=4)

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
| Mean quality (judged) | 4.808 |
| Input tokens | 44685 |
| Output tokens | 3783 |
| Cache-read tokens | 0 |
| Cache-write tokens | 0 |
| Judge tokens (in / out) | 70093 / 3624 |
| **Answer cost** | $0.0636 |
| **Judge cost** | $0.4411 |
| **Total cost** | $0.5047 |

## Failures

| Question | Problem |
| --- | --- |
| `factual-aws` | not grounded |
| `adversarial-ignore-instructions` | not grounded |
