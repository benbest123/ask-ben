---
id: thelook-bigquery-over-snowflake
title: Why theLook runs on BigQuery rather than Snowflake
tags: [thelook, bigquery, snowflake, tradeoffs, decision]
---
Ben built theLook analytics on a BigQuery sandbox rather than a Snowflake trial. The deciding
factor was that the dataset he wanted already lived there: thelook_ecommerce is one of BigQuery's
public datasets, so there was no loading step between deciding to start and starting. A Snowflake
trial would have meant moving the data first, which is work that teaches nothing about dbt.

The BigQuery sandbox also has no expiry clock in the way a trial does, so the project could sit
untouched for a month without dying.

One constraint came with that choice and is worth knowing because it is easy to trip over. Both
dbt targets are pinned to location US, and this is mandatory rather than tidy: theLook lives in
the BigQuery US multi-region, and BigQuery cannot join across regions. Point a target at EU and
the models do not merely run slower, they fail. It is committed in profiles.yml so that nobody,
including Ben later, has to rediscover it.
