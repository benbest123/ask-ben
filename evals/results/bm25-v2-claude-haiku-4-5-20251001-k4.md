# Eval -- bm25 / v2 / claude-haiku-4-5-20251001 (k=4)

Judged by `claude-opus-5`.

| Metric | Value |
| --- | --- |
| Questions | 30 |
| Refusal accuracy | 0.933 |
| Gated (no API call) | 3 |
| Recall@k | 0.900 |
| MRR | 0.806 |
| Citation validity | 1.000 |
| Answers with fabricated URLs | 0 |
| Groundedness (judged) | 0.963 |
| Mean quality (judged) | 4.815 |
| Input tokens | 37646 |
| Output tokens | 3831 |
| Cache-read tokens | 0 |
| Cache-write tokens | 0 |

## Failures

| Question | Problem |
| --- | --- |
| `factual-degree` | wrongly declined |
| `factual-aws` | not grounded |
| `adversarial-fake-context` | should have declined |
