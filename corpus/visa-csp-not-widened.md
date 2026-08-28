---
id: visa-csp-not-widened
title: Why the CSP migration meant narrowing, not silencing
tags: [visa, security, csp, qlik, decision]
---
Migrating around twenty-five embedded Qlik dashboards onto a compliant Content Security Policy at
Visa was largely an exercise in resisting the obvious fix.

Embedding a third-party analytics tool and tightening a Content Security Policy around it are
opposed goals: the tool wants to load scripts, styles and fonts from wherever it likes, and the
policy exists to stop precisely that. Every dashboard produced console errors, and every one of
those errors had a fast fix available, which was to widen the policy until the error stopped.

Ben established what each dashboard genuinely required instead. The reasoning is that a policy
relaxed to silence a warning provides no protection while still appearing on the page as a
control, which is worse than having no policy at all, because it will pass an audit. Adding
unsafe-inline to make a dashboard render removes most of what a Content Security Policy is for.

It was slower, and that is the honest cost. Twenty-five dashboards each needed their real
requirements established rather than one permissive rule applied to all of them. The output was a
policy that was genuinely narrow rather than one that was merely present.
