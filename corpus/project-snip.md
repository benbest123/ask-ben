---
id: project-snip
title: Snip, Ben's URL shortener
tags: [project, snip, typescript, nextjs, postgres, auth]
---
Snip is a full-stack URL shortener, live at snip-iota.vercel.app, built in TypeScript with
Next.js, PostgreSQL, Zod and deployed on Vercel. The repository is github.com/benbest123/url-shortener.

It has JWT authentication carried over httpOnly cookies, raw SQL against Postgres with no ORM,
and Zod validation on every API route.

Ben built it to do something end to end with no framework hand-holding: owning the schema, the
authentication and the deploy pipeline rather than inheriting them from a starter template. The
two choices that follow from that are the httpOnly cookie for the token, which keeps it out of
reach of any JavaScript running on the page and therefore out of reach of cross-site scripting,
and validating at the API boundary with Zod so that untrusted input is parsed into a known shape
once rather than checked repeatedly and inconsistently further in.

The no-ORM decision has its own entry in this corpus, because it is the one with a real cost
attached.
