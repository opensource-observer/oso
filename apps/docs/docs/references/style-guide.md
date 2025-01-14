---
title: Code Style Guide
sidebar_position: 10
---

## dbt Models

We generally follow the dbt style guides for mart and field names. We recommend reading through these official style guides first:

- [dbt directory structure](https://docs.getdbt.com/best-practices/how-we-structure/1-guide-overview)
- [dbt models](https://docs.getdbt.com/best-practices/how-we-style/1-how-we-style-our-dbt-models)

Optionally, there is an excellent blog piece on [best practices in naming for your stakeholders](https://docs.getdbt.com/blog/stakeholder-friendly-model-names)

In addition to the official guides, we follow these additional guidelines:

- **Use consistent naming**: Ensure consistent naming in all int tables. For example if we use `artifact_namespace`, do not rename this to _source_, _network_, _domain_, or _chain_ somewhere else.

- **Avoid complex marts**: Push all complexity to intermediate tables. Marts should simply be a direct copy or less granular version of an intermediate table.

- **Enumerate all columns explicitly in models**: concretely, this mean
  - Avoid using `*` statements in a mart model. This makes it easier to trace any changes through version control.
  - Avoid using positional arguments (i.e. `GROUP BY 1, 2, 3`). This can lead to easy bugs if columns get re-ordered
  - Avoid using acronyms or single-letter names. Prioritize easy-to-understand names over speed.
