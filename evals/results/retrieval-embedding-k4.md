# Retrieval-only eval -- embedding (k=4)

No generation, no judging, no Anthropic spend.

| Metric | Value |
| --- | --- |
| Questions | 30 |
| Recall@k | 0.989 |
| MRR | 0.983 |
| Gate accuracy | 0.767 |
| False refusals (real questions gated) | 0 |
| Missed refusals (off-topic let through) | 7 |
| Lowest answerable score | 0.275 |
| Highest off-topic score | 0.427 |
| Separation gap | -0.153 |

Gap interpretation: **the distributions overlap -- no single threshold separates them**.

