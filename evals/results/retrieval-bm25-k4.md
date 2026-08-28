# Retrieval-only eval -- bm25 (k=4)

No generation, no judging, no Anthropic spend.

| Metric | Value |
| --- | --- |
| Questions | 30 |
| Recall@k | 0.900 |
| MRR | 0.789 |
| Gate accuracy | 0.633 |
| False refusals (real questions gated) | 0 |
| Missed refusals (off-topic let through) | 11 |
| Lowest answerable score | 2.891 |
| Highest off-topic score | 16.200 |
| Separation gap | -13.309 |

Gap interpretation: **the distributions overlap -- no single threshold separates them**.

