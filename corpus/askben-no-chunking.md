---
id: askben-no-chunking
title: Why this widget has no chunking logic
tags: [ask-ben, rag, corpus, decision, tradeoffs]
---
There is no chunking code in this project. One markdown file is one chunk, and the corpus is
authored at chunk size, with each file deliberately written at roughly 150 to 320 words on a
single topic.

This declines the chunking problem rather than solving it. Splitting long documents well is
genuinely hard: fixed-size windows cut sentences in half, paragraph splits produce wildly uneven
chunks, and the overlap you add to compensate inflates the index and returns near-duplicate
results. None of that has to be solved if the source material never needs splitting.

Ben is direct about the limitation, because it is the obvious follow-up question. This does not
generalise. It works because the corpus is small, hand-written, and written specifically for this
purpose. The moment you point the system at documents you did not author, a PDF, a wiki export,
a set of transcripts, atomic authoring stops being available and a real chunking strategy becomes
unavoidable.

A test in the repository enforces the discipline by failing if any chunk exceeds 320 words, on
the reasoning that a 600-word chunk is a chunking problem wearing a disguise.
