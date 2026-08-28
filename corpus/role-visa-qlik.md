---
id: role-visa-qlik
title: The Qlik embedding layer Ben built at Visa
tags: [visa, react, nodejs, qlik, frontend, security]
---
Ben built the Qlik-embedding layer of a React and Node.js analytics microsite at Visa, covering
iframe orchestration and cross-frame communication, and migrated around twenty-five dashboards
onto a compliant Content Security Policy.

The CSP migration is the part worth asking about. Embedding a third-party analytics tool in an
iframe and then tightening a Content Security Policy around it are directly opposed goals: the
tool wants to load scripts, styles and fonts from wherever it likes, and the policy exists to
stop exactly that. Doing it for twenty-five dashboards meant establishing what each one genuinely
needed rather than widening the policy until the errors stopped, because a policy relaxed to
silence a console warning provides no protection while still looking like a control.

The cross-frame communication work sat alongside it. An embedded frame and its host page cannot
share a JavaScript context, so anything the host needs to know about the dashboard state has to
cross a message boundary that is itself part of the security surface.
