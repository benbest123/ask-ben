---
id: project-ask-ben
title: This question-answering widget
tags: [project, ask-ben, rag, llm, evaluation, python]
---
This widget is itself one of Ben's projects. It is a retrieval-augmented question answering
service over a curated corpus about his work: Python, FastAPI, Claude for generation, Voyage
embeddings for one of the retrievers, and no vector database. The repository is
github.com/benbest123/ask-ben.

He built it to have hands-on experience with large language model APIs that includes both prompt
design and real evaluation, rather than the usual demonstration that stops once something
responds.

The organising idea is that the corpus is small enough to fit in a single prompt, roughly ten to
fifteen thousand tokens. That makes the obvious challenge to the whole project fair: why build
retrieval at all when you could just send everything? Rather than argue about it, full-context
prompting is implemented as a control arm in the evaluation and measured against the two
retrievers. Where retrieval loses, the README says so.

The parts most likely to be interrogated in an interview carry measurements rather than
assertions: three prompt versions compared on outcomes, three retrieval strategies compared on
outcomes, and an evaluation whose language model judge is itself validated against Ben's own hand
labels before its scores are believed.
