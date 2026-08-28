---
id: how-i-work
title: How Ben works
tags: [meta, practices, testing, process]
---
A few habits show up across everything Ben builds, consistently enough to be worth stating as
practice rather than preference.

He works test-first. The test is written and watched to fail before the implementation exists,
because a test that has never been seen failing is a test whose behaviour is unverified rather
than confirmed. The question answering service producing this answer was built that way
throughout.

He treats a fix he cannot explain as unfinished. The race condition he debugged at Visa is the
example he uses: his first attempt made the symptom rarer without addressing the cause, and a
symptom that gets rarer is easy to mistake for one that is gone.

Every project runs lint, type checking and tests in CI on every pull request, and he works on
feature branches with pull requests rather than committing to the main branch, including on
repositories where he is the only contributor.

He writes decisions down with their rejected alternatives attached. Most entries in this corpus
take that form: the choice, the thing not chosen, and the condition under which the answer would
change. A decision recorded without its alternative is indistinguishable from a default, and the
most useful thing to know about any technical choice is what would have to be true for it to be
wrong.
