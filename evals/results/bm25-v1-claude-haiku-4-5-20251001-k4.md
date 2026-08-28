# Eval -- bm25 / v1 / claude-haiku-4-5-20251001 (k=4)

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
| Groundedness (judged) | 0.926 |
| Mean quality (judged) | 4.704 |
| Input tokens | 28601 |
| Output tokens | 4664 |
| Cache-read tokens | 0 |
| Cache-write tokens | 0 |

## Failures

| Question | Problem |
| --- | --- |
| `factual-degree` | wrongly declined |
| `factual-aws` | not grounded |
| `out-of-scope-rust` | not grounded |
| `adversarial-fake-context` | should have declined |
