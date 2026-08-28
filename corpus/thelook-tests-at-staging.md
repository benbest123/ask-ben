---
id: thelook-tests-at-staging
title: Why theLook's tests live at staging, not on sources
tags: [thelook, dbt, testing, decision]
---
theLook analytics has fifty tests and they sit at the staging layer rather than on the sources.

The reasoning is specific to this project's circumstances. Staging is a one-to-one view over a
static, read-only public dataset. Testing the source as well would run essentially the same
assertions twice, at double the query cost, and there is no upstream team to attribute a failure
to even if one occurred.

Ben is explicit that this reasoning inverts the moment there is a real upstream owner. Against a
live source with a team behind it, source tests and freshness checks are exactly where a failure
gets attributed correctly, because the whole value of a source test is that it says the problem
arrived rather than that it was introduced here.

One related habit from the same project is worth mentioning: he proves a test can fail before
trusting it. A test that has never been observed failing is a test whose behaviour is unverified.
Hand-verifying aggregates against staging for a sample user found a real bug that had compiled
cleanly, returned plausible numbers, and passed every generic test in the project, because
generic tests constrain structure rather than arithmetic.
