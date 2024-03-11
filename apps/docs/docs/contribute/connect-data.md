---
title: Connect Your Data
sidebar_position: 4
---

:::info
We're always looking for new data sources to integrate with OSO and deepen our community's understanding of open source impact. If you're a developer or data engineer, we'd love to partner with you to connect your database (or other external data sources) to the OSO data warehouse.
:::

## CloudQuery Plugins

---

[CloudQuery](https://cloudquery.io) is used to integrate external data sources
into the Open Source Observer platform. At this time we are limiting the
CloudQuery plugins in the OSO repository to Python or Typescript.

This page will go over writing a plugin with Python, which is our suggested plugin language.

### Getting Started

:::warning
At the moment, this isn't a full tutorial on writing a CloudQuery plugin. For
now, this will just get you started on the boilerplate required to create a new
one. To see the full documention for writing a plugin, use the [CloudQuery
Docs](https://docs.cloudquery.io/docs/developers/creating-new-plugin/python-source).
:::

_This guide assumes some knowledge of Python and the command line._

Before we begin you'll need at least the following installed:

- git
  - [Official
    Instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  - If you're on macOS, we suggest using [homebrew](https://brew.sh/)
- Python 3.11+
  - All of our code has been tested on this version. Previous versions may
    work but this isn't suggested.
- [Poetry](https://python-poetry.org/)
  - We use this for managing dependencies of our Python projects.
- CloudQuery CLI
  - [Linux](https://docs.cloudquery.io/docs/quickstart/linux)
  - [macOS](https://docs.cloudquery.io/docs/quickstart/macOS)
  - [Windows](https://docs.cloudquery.io/docs/quickstart/windows) _Note:
    CloudQuery supports windows but no OSO code has been tested on windows. We
    would assume bash on windows would support the repository but this hasn't
    been validated_

### Clone the `oso` repository

The [oso](https://github.com/opensource-observer/oso) repository is where all of
the infrastructure code and data pipelines live.

Clone this with the following:

```bash
git clone https://github.com/opensource-observer/oso.git
```

And, `cd` into the repository:

```bash
cd oso
```

### Install OSO Python dependencies

For updating the data pipelines and CloudQuery plugins, we only currently care
about the Python dependencies. To install these dependencies, we will use
python's `poetry` from the root of the OSO repository:

```bash
poetry install
```

Once you've done this, let's enter the Python virtual environment that `poetry`
created:

```bash
poetry shell
```

### Starting a new plugin

To make this as simple as possible, we've created an example plugin that can be
duplicated and used to create a new plugin. Let's do this by calling the
following from the root of the OSO repository (feel free to use a name besides
`cloudquery-my-plugin`):

```bash
cp -r warehouse/cloudquery-example-plugin warehouse/cloudquery-my-plugin
```

### Update the `pyproject.toml` file

You'll need to update the `pyproject.toml` file within the plugin directory with
the proper naming of your new plugin and add any dependencies you may need. It's
important that you use a name that is unique to the plugin within the oso
repository.

Assuming we need the `requests` added to the dependencies. This is what your
`pyproject.toml` should look like:

```toml
[tool.poetry]
name = "cloudquery-my-plugin" # Update this to the plugin name
version = "0.1.0"
description = "Description for the plugin"
authors = ["Kariba Labs"]
license = "Apache-2.0"
readme = "README.md"
packages = [{ include = "my_plugin" }] # Update `my_plugin` this to the plugin name

[tool.poetry.dependencies]
python = "^3.11"
cloudquery-plugin-sdk = "^0.1.12"
requests = "^2.31.0"

[tool.poetry.scripts]
my_plugin = 'my_plugin.serve:run' # Update `my_plugin` to the plugin name

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### Adding the plugin to the poetry configuration at the top of the repo

The OSO repository is structured as a monorepo (for both node and python
projects). So in order to properly manage the repo's dependencies you'll need to
add your plugin to the monorepo at the root of the repository.

Within the `pyproject.toml` at the root of the repository, under the
`[tool.poetry.dependencies]` section, make it appear like so, with your plugin's
directory:

```toml
[tool.poetry.dependencies]
python = "^3.11"
example-plugin = { path = "warehouse/cloudquery-example-plugin", develop = true }
my-plugin = { path = "warehouse/cloudquery-my-plugin", develop = true }
```

### Installing the dependencies for the new plugin

To install the dependencies of the new plugin make sure you're in the root of
the OSO repository and run the following:

```bash
poetry update
```

This will add the new plugin and also will add a script on the `PATH` for the
new plugin at `my_plugin` (or whatever name you used).

### Updating dependencies

Any time you update dependencies in the plugin just run:

```bash
poetry update
```

### Developing the plugin

As noted in a previous disclaimer, this doc isn't (_yet_) a full tutorial on
writing a CloudQuery plugin. For now, this will just get you started on the
boilerplate required to create a new one. To see the full documention use the
[CloudQuery
Docs](https://docs.cloudquery.io/docs/developers/creating-new-plugin/python-source)

### Packaging the plugin

Once you've finished developing the plugin, you'll need to package the plugin
for use. Luckily, the `oso` repository is automatically configured to handle
packaging all plugins in the `cloudquery` directory as long as they're Python or
TypeScript plugins. So, as long as you have followed this guide the automation
in the repository will handle properly building, packaging, and publishing a
docker image for your CloudQuery plugin.

### Adding your plugin to the data pipeline

In the future the data pipeline will likely be managed by [Dagster](https://dagster.io/) or something
similar, however at this time the entire data pipeline lives in a single
[workflow on GitHub](https://github.com/opensource-observer/oso/actions/workflows/warehouse-run-data-pipeline.yml) and is run every 24 hours at 02:00 UTC.

To add your plugin to that workflow you will need to do 2 things:

- Add a CloudQuery yml config file for your plugin
- Add a step to execute your plugin in the github action

#### Adding a CloudQuery yml config

The configurations live in `.github/workflows/cloudquery`. Create a file for
your workflow here that is named the same as your new plugin. It will need to
use some environment variables so that our pipeline will be able to properly
target both your plugin's Docker deployment and also the correct BigQuery
dataset.

It should look something like this:

```
kind: source
spec:
  name: my-plugin

  # ${DOCKER_TAG} is automatically injected by the pipeline
  # and will point to the latest build of the CloudQuery plugin
  path: "ghcr.io/opensource-observer/my-plugin:${DOCKER_TAG}"
  registry: "docker"
  version: "v0.0.1"
  tables:
    ["*"]
  destinations:
    - "bigquery"
---
# The destination section _must_ be configured minimally with these settings
kind: destination
spec:
  name: bigquery
  path: cloudquery/bigquery
  registry: cloudquery
  version: "v3.3.13"
  write_mode: "append"
  spec:
    project_id: ${DESTINATION_PROJECT_ID}
    dataset_id: ${DESTINATION_BIGQUERY_DATASET}
```

#### Adding a step in the data pipeline

The data pipeline's github action can be found in
`.github/workflows/warehouse-run-data-pipeline.yml`. Unless necessary to run
before the oss-directory workflows, we suggest running any plugin _after_ the
step named `Run cloudquery for github-resolve-directory` and it _must_ run
before `Setup dbt`.

So to add your step. You will simply need to add this section in between those
two steps like so (make sure you're using the correct indentation)

```yml
- name: Run cloudquery for github-resolve-directory
  run: |
    docker run -d --rm -p 7777:7777 \
      -v ${CLOUDQUERY_FILE_DIRECTORY}:${CLOUDQUERY_FILE_DIRECTORY} \
      --name github-resolve-repos \
      ghcr.io/opensource-observer/cloudquery-github-resolve-repos:${DOCKER_TAG} \
      serve --address 0.0.0.0:7777 &&
    cloudquery sync .github/workflows/cloudquery/github-resolve-repos.yml --log-level debug --log-console &&
    docker stop github-resolve-repos

# YOUR NEW PLUGIN GOES HERE
- name: Run cloudquery for my-plugin
  run: |
    cloudquery sync .github/workflows/cloudquery/my-plugin.yml --log-level debug --log-console

- name: Setup dbt
  run: |
    bash .github/scripts/create-dbt-profile.sh opensource_observer ${GOOGLE_APPLICATION_CREDENTIALS} &&
    cat ~/.dbt/profiles.yml && 
    gcloud auth list
```

In the future we intend to improve the experience of adding a plugin to the
pipeline, but for now these docs are consistent with the current state of the
pipeline.

## Airbyte Connectors

---

Deploy Airbyte connectors to index data from new sources.

:::warning
This section is a work in progress.
:::

- Go over creating a simple airbyte connector to a sample API
- Go over creating a simple airbyte connector to an already existing public dataset
