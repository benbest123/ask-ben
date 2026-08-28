---
id: role-visa-solo-cover
title: Five weeks holding Qlik alone during a cloud migration
tags: [visa, qlik, infrastructure, ownership, debugging]
---
For five weeks, Ben independently maintained the Qlik dashboards and Qlik infrastructure through
the absence of the team senior engineer, a stretch that happened to coincide with a company-wide
on-premise-to-cloud migration. He worked alongside the operations team to resolve configuration
and infrastructure issues as they arose.

Two pieces of engineering came out of that period. The first was a reliable load-completion
detection mechanism for third-party dashboards that exposed no official data-ready API, so there
was no supported way to ask whether a dashboard had finished loading. The second was a data race
condition in the async provisioning flow, which he debugged and fixed after an initial attempt
using polling turned out to be the wrong shape of solution.

The circumstances are the part worth noting as much as the code. Sole ownership of a system
during a migration means every problem arrives without anyone more senior to escalate it to, and
the migration itself was generating most of them.

The race condition has its own entry in this corpus, because the first fix being wrong is the
useful part.
