---
id: role-visa-qlik
title: The Qlik embedding layer Ben built at Visa
tags: [visa, react, nodejs, qlik, frontend, security]
---
Ben built the Qlik-embedding layer of a React and Node.js analytics microsite at Visa, covering
iframe orchestration and cross-frame communication, and migrated around twenty-five dashboards
onto a compliant Content Security Policy.

The cross-frame work exists because an embedded frame and its host page cannot share a JavaScript
context. Anything the host needs to know about the state of the dashboard inside the frame has to
cross a message boundary, and that boundary is itself part of the application's security surface
rather than a convenience.

Alongside this he delivered SQL Server stored procedures and end-to-end Google Analytics
instrumentation across a multi-tenant .NET monolith, covering per-partner enablement, server-side
initialisation, security-header updates and form event capture.

This was the more software-focused half of his time at Visa, and the reason he is open to
software engineering roles as well as data ones. The reasoning behind how the Content Security
Policy migration was approached has its own entry in this corpus.
