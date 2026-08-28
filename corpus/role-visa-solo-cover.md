---
id: role-visa-solo-cover
title: Five weeks holding Qlik alone during a cloud migration
tags: [visa, qlik, infrastructure, ownership, debugging]
---
For five weeks, Ben independently maintained the Qlik dashboards and Qlik infrastructure through
the absence of the team senior engineer, a stretch that happened to coincide with a company-wide
on-premise-to-cloud migration. He worked alongside the operations team to resolve configuration
and infrastructure issues as they surfaced.

Two technical problems from that period are worth the detail. The first was load-completion
detection for third-party dashboards that exposed no official data-ready API: there was no
supported way to ask whether a dashboard had finished loading, so the question became how to know
something reliably without the system telling you. The second was a data race condition in the
async provisioning flow, which he debugged and fixed.

The second is the better story because the first attempt was wrong. He started with polling,
which worked until it did not: polling answers whether something is ready now, and a race needs
to know whether it was ready before some other thing happened. He iterated to a timestamp-based
heuristic, which addressed the ordering rather than the timing.
