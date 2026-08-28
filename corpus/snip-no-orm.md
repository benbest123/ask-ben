---
id: snip-no-orm
title: Why Snip uses raw SQL and no ORM
tags: [snip, sql, postgres, tradeoffs, decision]
---
Snip talks to Postgres in raw SQL with no ORM. This was the point of the project rather than an
oversight: Ben built it specifically to work end to end with no framework hand-holding, and an
ORM is the single largest piece of hand-holding available in that stack.

What he wanted from it was ownership of two things an ORM tends to take over. The first is the
schema, including what the indexes and constraints actually are rather than what a set of model
classes implies they should be. The second is the query plan, because with an ORM the SQL that
reaches the database is generated, and the distance between what you wrote and what ran is where
performance surprises live.

The cost is real and he does not pretend otherwise: it is more boilerplate, every query has to be
written and maintained by hand, and nothing stops a typo in a column name until runtime. Zod
validation at the API boundary covers the input side of that, but not the SQL itself.

For a production application with a large team and a wide schema, he would expect that
calculation to come out the other way.
