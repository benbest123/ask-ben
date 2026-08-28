---
id: role-visa-billing-pipeline
title: The partner billing pipeline Ben led at Visa
tags: [visa, aws, etl, leadership]
---
As feature lead at Visa, Ben designed and delivered an AWS data pipeline producing monthly
billing and reporting data for eight banking partners.

The ETL ran on AWS Glue using PySpark. The infrastructure was provisioned with AWS CDK in
TypeScript, giving each partner its own S3 bucket, Glue job, KMS key and IAM role, so that the
isolation between partners was enforced by AWS permissions rather than by application logic.
Onboarding a further partner was a configuration change rather than a manual setup exercise.

Feature lead here meant owning the design and the delivery rather than managing people: deciding
how the pipeline was structured, how the partner boundary was drawn, and how the infrastructure
was expressed, then building it and seeing it into production.

It was the largest single piece of work in his time at Visa and the one he points to first. The
reasoning behind the isolation model has its own entry in this corpus.
