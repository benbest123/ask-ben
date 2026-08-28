---
id: askben-no-vector-db
title: Why this widget has no vector database
tags: [ask-ben, rag, architecture, decision, yagni]
---
This question answering service uses no vector database. There is no Pinecone, no Chroma, no
pgvector. Retrieval is either a BM25 score over the chunks or a numpy dot product against a
matrix of embeddings that is committed to the repository.

The corpus is around thirty chunks. Embedded at 1024 dimensions that is a matrix of roughly
thirty by one thousand and twenty-four floats, which is about 120 kilobytes and fits comfortably
in memory. A brute-force comparison against every chunk is a single matrix multiplication taking
well under a millisecond. Approximate nearest neighbour search exists to avoid comparing against
everything, and at this size comparing against everything is already the fast path.

So a vector database would be a network hop, an API key, a second thing that can be down, and an
index that can silently drift out of sync with the corpus, in exchange for solving a problem that
does not exist yet.

Ben is clear about where the answer changes. This holds while the corpus fits in memory and
rebuilding the index is cheap. Somewhere in the low tens of thousands of chunks, or as soon as
the corpus updates continuously rather than by a commit, the calculation inverts.
