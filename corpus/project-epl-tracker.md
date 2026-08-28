---
id: project-epl-tracker
title: EPL Score Tracker
tags: [project, epl, react, nodejs, rest-api, postgres]
---
The EPL Score Tracker is a Premier League score tracker: a React front end over a Node and
Express backend that syncs fixture data from an external API into Postgres and serves it over
REST. The backend repository is github.com/benbest123/epl-tracker-backend.

Ben built it to practise designing a REST API and a sync job against a third-party feed he did
not control, which is a different problem from querying a database you own. A feed you do not
control can be slow, rate-limited, temporarily wrong, or shaped differently from what your schema
expects, and the sync job is where all of that has to be absorbed before it reaches anything
else.

It is not deployed, and the reason is worth stating rather than hiding: the free tier of the
fixture API omits the current season, so a live deployment would show an empty or stale table.
Ben's personal site marks it as running locally rather than live for that reason. No project on
the site claims a deployment it does not have.
