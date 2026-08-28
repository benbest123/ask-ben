---
id: visa-isolation-in-iam-not-code
title: Why partner isolation lived in IAM, not application code
tags: [visa, aws, iam, security, decision]
---
On the partner billing pipeline at Visa, each of the eight banking partners got its own S3
bucket, Glue job, KMS key and IAM role. The alternative, and the one most teams reach for first,
is a shared bucket with a partner identifier on each row and application code that filters by it.

Ben drew the boundary in IAM and KMS instead, and the reason is what happens when someone is
wrong. If isolation is enforced in application code, then a mistaken join, a missing WHERE clause
or a mis-set variable puts one bank's billing data in another bank's report, and nothing stops
it, because the code has permission to read everything. If isolation is enforced in IAM, the same
mistake fails: the role cannot read the other bucket and the job errors instead of quietly
producing a wrong number.

The second half of the decision was defining it in AWS CDK rather than clicking it into the
console. That made onboarding a ninth partner a configuration change rather than a manual walk
through several services, and more importantly it made the isolation reviewable in a pull request
rather than trusted to whoever configured it last and remembered correctly.

The cost is more infrastructure objects to manage. At eight partners that was clearly worth it.
