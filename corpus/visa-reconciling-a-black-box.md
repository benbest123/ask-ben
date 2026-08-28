---
id: visa-reconciling-a-black-box
title: How to replace a system nobody can read
tags: [visa, migration, data-quality, decision]
---
Replacing the legacy billing process at Visa posed a problem that the SQL itself did not. The old
process was authoritative, in the sense that whatever it produced was by definition what the
business had been billing, but nobody could say precisely how it produced it.

That changes the goal. The target was not to build a correct pipeline, because there was no
independent definition of correct to build towards. It was to build a pipeline whose every
difference from the old one could be explained.

So each discrepancy became a question rather than a defect: either the new pipeline was wrong, or
the old one had been, and the work was being able to say which, with a reason. Some differences
turned out to be the new pipeline being right, and those are the ones that need the most
evidence, because fixing them means telling someone their historical numbers were wrong.

Change-data-capture deduplication mattered for the same underlying reason. Double-counting a
restated transaction does not produce an obviously broken figure, it produces a plausible one, so
it never announces itself. The general principle Ben works from is that in billing and financial
data, the dangerous failures are the ones that still look reasonable.
