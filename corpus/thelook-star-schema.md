---
id: thelook-star-schema
title: Why theLook uses a layered star schema
tags: [thelook, dbt, modelling, star-schema, decision]
---
theLook analytics is modelled as a layered star schema: sources feed thin staging views, one per
source table doing renaming and recasting with no joins, and the marts on top hold fact and
dimension tables.

The alternative Ben considered and rejected was one big table, a single wide denormalised table
containing everything. That is not a strawman. On columnar storage a wide table often performs
better, because the engine reads only the columns a query touches and there are no joins to
execute at all.

He chose the star anyway, and the reason is maintainability rather than speed: the star keeps
each definition in exactly one place. In a wide table, a business definition such as what counts
as a completed order gets re-expressed everywhere it is needed, and the copies drift.

The tradeoff is deliberate and it is size-dependent, which is the part worth saying out loud. At
this scale the query-speed cost is irrelevant and the maintainability gain is real. At a scale
where the join cost actually shows up in query bills, the same reasoning would come out
differently.
