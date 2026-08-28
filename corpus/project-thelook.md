---
id: project-thelook
title: theLook analytics, Ben's dbt project
tags: [project, thelook, dbt, bigquery, sql, data-modelling]
---
theLook analytics is a dbt project over BigQuery's public thelook_ecommerce dataset: staging
models, a star schema of fact and dimension tables, tests, and generated documentation. Eight
models, fifty tests, and CI that builds the whole graph on every pull request. The repository is
github.com/benbest123/thelook-analytics. It runs locally and in CI rather than being deployed as
a service, which is what a dbt project is.

Ben built it to learn dbt's model, test and documentation workflow end to end. Using a public
dataset was a deliberate choice on two counts: it needs no cleaning, so the modelling is the
point rather than the janitorial work, and a reviewer already knows the data well enough to judge
whether the schema is any good.

The structure is layered. Sources feed thin staging views, one per source table, doing renaming
and recasting with no joins; the marts on top hold the fact and dimension tables. Several of the
decisions behind it have their own entries in this corpus, including why the tests live at
staging rather than on sources, and why margin in the project is deliberately approximate.
