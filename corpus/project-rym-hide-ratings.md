---
id: project-rym-hide-ratings
title: RYM Hide Ratings, Ben's Firefox extension
tags: [project, browser-extension, javascript, firefox, shipping]
---
RYM Hide Ratings is a Firefox extension that hides RateYourMusic ratings on a release page until
you have rated it yourself. It is published on the Mozilla add-ons store and the repository is
github.com/benbest123/rym-hide-ratings. It is written in JavaScript against the WebExtensions
API.

Ben built it partly to scratch his own itch, which is that seeing an aggregate score before
listening anchors your own opinion to it, and partly to learn what shipping through a real review
process actually involves.

That second half is the reason it is on his site at all. It is a small piece of JavaScript, but
it is the only one of his projects that went through an external reviewer with the power to
reject it: manifest permissions have to be justified and minimal, the listing has to satisfy
store policy, and updates go through the same gate again. Requesting the narrowest set of
permissions that still does the job is a different discipline from writing code that works.
