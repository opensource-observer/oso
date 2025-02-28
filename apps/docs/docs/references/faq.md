---
title: FAQs
sidebar_position: 9
---

## Community

### How is OSO supported?

Open Source Observer is a public good.
All of our code is [open source](https://github.com/opensource-observer/oso/).
All of our data sets and models are [open data](../integrate/datasets/index.mdx).
All of our infrastructure is [open](https://dagster.opensource.observer/locations) too.
If we are going to transform funding for public goods,
we need to live by an open source ethos.
We are supported by grants from our generous partners, which pay for
the platform development, running the data pipeline regularly,
and community incentives for data and insights.
If you want to support us, please reach out at
[info@karibalabs.co](mailto:info@karibalabs.co).

### I'm brand new. How do I get started?

Join our [Discord](https://www.opensource.observer/discord).
This is where we hang out most of the time and usually the best place
to introduce yourself and ask questions.
If you know what you're looking for, our docs are the best place
to search for the answer.
We do also occasionally host public
[data challenges](../contribute-models/challenges/index.md)
if you're looking for more structure.

---

## Data

### How can we analyze different open source ecosystems?

Our ambition with OSO is to transform how we measure impact
across _any_ open source ecosystem.
However, you'll notice that most of our existing data
is skewed towards certain ecosystems that we work with closely.
In order to instruct the indexer to also analyze your project,
you must add your project to
[oss-directory](https://github.com/opensource-observer/oss-directory/).
We have detailed instructions on how to do that
[here](../projects).

### How often do you index / refresh your data?

Our data pipeline currently is set to run weekly (on Sundays).
Our existing setup involves large jobs that take days to complete.
We are working on optimizing our performance and cost structure
so that we can run this more frequently.

---

## Product

### How can I request a new feature?

We live and breathe in our
[GitHub issues](https://github.com/opensource-observer/oso/issues/).
In order to help us triage, please search to see if an existing issue
already exists for your request before filing a new issue.
You can monitor our progress on our
[project board](https://github.com/orgs/opensource-observer/projects/3/views/10).

### How is OSO different from XYZ tool?

What distinguishes OSO is the power of our community,
where every part of our stack is supported by a diverse network of contributors, including:

- data indexers who provide various raw data sources
- data modelers who help us refine our metrics and data models
- data engineers who keep the pipeline running smoothly
- data integrations that share OSO metrics and insights across various applications

Together, we are building a rich dependency tree of open data sets,
which you can see on our
[Dagster dashboard](https://dagster.opensource.observer/assets).
Every data asset is maintained by a dedicated contributor and refreshed regularly.
Each contributor has their own upstream dependencies and downstream dependents.
New contributors can build on any existing data asset, including hundreds
of incredible intermediate models, from user reputation models to retention/churn models.
We are building the biggest data network with the best open source community.
