---
id: how-i-work
title: How Ben works
tags: [meta, practices, testing, process]
---
A few habits show up across everything Ben builds, and they are consistent enough to be worth
stating as practice rather than preference.

He works test-first. The test is written and watched to fail before the implementation exists,
because a test that has never been seen failing is a test whose behaviour is unverified. On
theLook analytics this caught a real bug in an aggregate that compiled cleanly, returned
plausible numbers, and passed every generic test in the project.

Every project runs lint, type checking and tests in CI on every pull request, and he works on
feature branches with pull requests rather than committing to the main branch, including on
repositories where he is the only contributor.

He writes decisions down with their rejected alternatives attached. Most of the entries in this
corpus are in that form: the choice, the thing that was not chosen, and the condition under which
the answer would change. His view is that a decision recorded without its alternative is
indistinguishable from a default, and that the most useful thing to know about any technical
choice is what would have to be true for it to be wrong.
