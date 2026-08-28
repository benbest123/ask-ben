---
id: role-visa-legacy-billing
title: Replacing a black-box billing process at Visa
tags: [visa, spark, sql, data-warehouse, migration]
---
Ben recreated a legacy black-box billing process as a transparent Spark SQL pipeline over a cloud
data warehouse. It aggregated transaction-level payment data into per-company monthly metrics,
handling currency conversion and change-data-capture deduplication along the way.

The interesting part of this kind of work is not the SQL. It is that the old process was
authoritative, in the sense that whatever it produced was by definition what the business had
been billing, but nobody could say precisely how it produced it. So the target was not to build a
correct pipeline. It was to build a pipeline whose differences from the old one could each be
explained. Reconciling against a system you cannot read means every discrepancy is a question
rather than a bug: either the new pipeline is wrong or the old one was, and you have to be able
to say which.

Change-data-capture deduplication mattered for the same reason. Double-counting a restated
transaction produces a plausible number, not an obviously broken one, so it fails quietly.
