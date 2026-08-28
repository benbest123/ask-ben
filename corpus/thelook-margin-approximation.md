---
id: thelook-margin-approximation
title: Why margin in theLook is approximate
tags: [thelook, dbt, modelling, tradeoffs, known-limitation]
---
Margin in theLook analytics is computed against the current catalogue cost of a product, not the
cost at the time of sale. That makes it approximate, and the more serious consequence is that it
makes it irreproducible: rerun the project after a cost changes and historical margins move.

Ben chose this knowingly rather than by accident. The public theLook dataset carries no cost
history, so the alternative was to invent one.

The honest fix needs two things together, and that is the part he can explain. An SCD2 snapshot
on product cost gives you what the cost was on a given date. But a fact table that is fully
rebuilt every run cannot freeze anything by definition, so the fact also has to become
incremental, so that settled rows are never recomputed. Doing only the first half would not
work.

He did not build it because the project's purpose was to learn dbt's model, test and
documentation workflow, and snapshots plus incrementality would have added two large concepts
before the first was solid. The limitation is written down in the project's README rather than
hidden, and that is the part that matters: an approximation you have documented is a decision,
and one you have not is a bug.
