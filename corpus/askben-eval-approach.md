---
id: askben-eval-approach
title: How this widget is evaluated
tags: [ask-ben, evaluation, llm-judge, metrics, decision]
---
The evaluation is the point of this project rather than an accessory to it.

It runs against a golden set of roughly thirty questions in four deliberate categories:
answerable factual questions, answerable questions that require reasoning across chunks,
out-of-scope questions that should be refused, and adversarial prompt-injection attempts.

The metrics are split into two tiers on the basis of cost. Deterministic ones are free and run on
every pull request: whether cited chunk ids are valid, whether out-of-scope questions were
actually refused, and recall at k and mean reciprocal rank measured against a must-cite field on
each question. That last pair is what separates a retrieval failure from a generation failure,
which otherwise look identical from the outside. Judged metrics cost money, so they run on manual
dispatch only.

The part Ben would point to first is that the language model judge is itself validated. Using a
model to grade a model is circular if you stop there, so the judge's verdicts are compared
against roughly twenty questions Ben labelled by hand, and the agreement rate is reported
alongside every score the judge produces. If the judge and the human disagree badly, the judge's
numbers do not get believed.
