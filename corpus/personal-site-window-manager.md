---
id: personal-site-window-manager
title: Why the personal site is built around a window manager
tags: [personal-site, react, state-management, reducer, decision]
---
Ben's personal site renders a Windows 95 desktop with draggable, focusable, minimisable windows,
and the whole thing is built on a pure reducer.

The stated reason for the site is that he wanted somewhere to put his CV that is more memorable
than a PDF. The real engineering reason is the second one he gives: a window manager is a
genuinely interesting piece of state modelling.

That is what makes the choice defensible rather than decorative. Window management is a nest of
interacting state that is easy to get subtly wrong: z-order, which window has focus, what happens
to focus when the focused window is minimised or closed, and how a drag in progress interacts
with all of it. Modelling that as a pure reducer means every transition is a function from state
and action to new state, with no timers or DOM measurements hidden inside, so the awkward cases
can be tested directly as a sequence of actions rather than by driving a browser.

The visual theme is the part people notice. The reducer is the part worth reviewing.
