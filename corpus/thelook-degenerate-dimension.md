---
id: thelook-degenerate-dimension
title: Why order_id is a degenerate dimension in theLook
tags: [thelook, dbt, modelling, dimensional-modelling, decision]
---
In theLook analytics, order_id sits on the fct_order_items fact table with no dim_orders table
behind it. That makes it a degenerate dimension: an identifier kept on the fact for grouping and
counting, rather than a foreign key pointing at a dimension.

The reason is that there was nothing to put in dim_orders. Every order attribute in this dataset
is either already on the item rows or already on dim_users, so the table would have held an
identifier and nothing else, which is a join for no information.

The framing Ben uses matters more than the decision. order_id is degenerate relative to this
model, not intrinsically. The moment there are genuine order-level measures, shipping cost being
the obvious one, the right structure becomes a header and line split: fct_orders alongside
fct_order_items, at two different grains. Shipping cost cannot live on the item fact without
being either duplicated across every line or allocated arbitrarily between them, and both of
those are ways of getting the wrong answer later.

So it is a decision with a stated trigger for revisiting it rather than a permanent judgment.
