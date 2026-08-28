---
id: visa-polling-to-timestamp
title: Getting a race condition wrong before getting it right
tags: [visa, debugging, concurrency, decision]
---
During the five weeks Ben held Qlik alone at Visa, he debugged a data race condition in the async
provisioning flow. His first fix was wrong, which is why it is the story he tells.

He started with polling: check whether the resource is ready, wait, check again. That worked in
testing and kept failing intermittently in practice. The reason is that polling answers the
question of whether something is ready now, and a race condition is not a question about now. It
is a question about ordering: was this ready before that other thing happened? Polling more
frequently narrows the window without closing it, so a polling fix to a race looks like it is
working right up until it is not.

He replaced it with a timestamp-based heuristic, which compares when things happened rather than
sampling whether they have happened, and that addressed the ordering directly.

The general lesson he takes from it is about diagnosis rather than concurrency. The first fix
made the symptom rarer, and a symptom that gets rarer is easy to mistake for one that is gone.
The tell was that he could not explain why it worked, only that it seemed to.
