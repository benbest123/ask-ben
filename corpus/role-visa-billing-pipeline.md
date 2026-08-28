---
id: role-visa-billing-pipeline
title: The partner billing pipeline Ben led at Visa
tags: [visa, aws, etl, leadership]
---
As feature lead at Visa, Ben designed and delivered an AWS data pipeline producing monthly
billing and reporting data for eight banking partners. The ETL ran on AWS Glue using PySpark, and
the infrastructure was provisioned with AWS CDK in TypeScript: separate S3 buckets, Glue jobs,
KMS keys and IAM roles for each partner.

The per-partner isolation was the point rather than an implementation detail. Billing data for
one bank must not be reachable from another partner role, so the boundary was drawn in IAM and
KMS rather than in application code, where a bug could cross it. Defining that in CDK meant
adding a ninth partner became a configuration change rather than a manual walk through the
console, and it meant the isolation was reviewable in a pull request instead of trusted to
whoever clicked last.

Feature lead here meant owning the design and the delivery, not managing people.
