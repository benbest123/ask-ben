---
id: project-personal-site
title: Ben's personal site
tags: [project, personal-site, react, typescript, vite, frontend]
---
Ben's personal site at benbest.uk is a Windows 95 desktop rendered in the browser: a custom
window manager with draggable, focusable, minimisable windows, built on a pure reducer. It is
React and TypeScript with Vite, Tailwind and 98.css, deployed on Vercel, and the repository is
github.com/benbest123/personal-site.

He built it for two reasons. The first is that he wanted somewhere to put his CV that is more
memorable than a PDF. The second is the honest one: a window manager is a genuinely interesting
piece of state modelling, which is a better reason to build something than the fact that it looks
nice.

The site is a static build, which is the constraint that made the hosting decision cheap. Vercel
auto-detects the Vite preset, so there is no configuration file and no build overrides, and any
static host would serve the output equally well. That reversibility was the point of the choice
rather than a side effect. This question answering widget is the first thing to break the static
rule, which is why it lives in a separate repository.
