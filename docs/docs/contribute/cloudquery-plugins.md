---
title: CloudQuery Plugins
sidebar_position: 6
---

Create a CloudQuery plugin to integrate external data sources into the Open Source Observer data warehouse.

[CloudQuery](https://cloudquery.io) is used to integrate external data sources
into the Open Source Observer platform. At this time we are limiting the
cloudquery plugins in the OSO repository to Python or Typescript. This page will
go over writing a plugin with python, which is our suggested plugin language.

## Getting Started

:::warning
At the moment, this isn't a full tutorial on writing a CloudQuery plugin. For
now, this will just get you started on the boilerplate required to create a new
one. To see the full documention for writing a plugin, use the [CloudQuery
Docs](https://docs.cloudquery.io/docs/developers/creating-new-plugin/python-source).
:::

_This guide assumes some knowledge of python and the command line._

Before we begin you'll need at least the following installed:

- git
  - [Official
    Instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  - If you're on macOS, we suggest using [homebrew](https://brew.sh/)
- Python 3.11+
  - All of our code has been tested on this version. Previous versions may
    work but this isn't suggested.
- [Poetry](https://python-poetry.org/)
  - We use this for managing dependencies of our python projects.
- CloudQuery CLI
  - [Linux](https://docs.cloudquery.io/docs/quickstart/linux)
  - [macOS](https://docs.cloudquery.io/docs/quickstart/macOS)
  - [Windows](https://docs.cloudquery.io/docs/quickstart/windows) _Note:
    CloudQuery supports windows but no OSO code has been tested on windows. We
    would assume bash on windows would support the repository but this hasn't
    been validated_

## Clone the `oso` repository

The [oso](https://github.com/opensource-observer/oso) repository is where all of
the infrastructure code and data pipelines live.

Clone this with the following:

```bash
$ git clone https://github.com/opensource-observer/oso.git
```

And, `cd` into the repository:

```bash
$ cd oso
```

## Install oso python dependencies

For updating the data pipelines and cloudquery plugins, we only currently care
about the python dependencies. To install these dependencies, we will use
python's `poetry` from the root of the oso repository:

```bash
$ poetry install
```

Once you've done this, let's enter the python virtual environment that `poetry`
created:

```bash
$ poetry shell
```

## Starting a new plugin

To make this as simple as possible, we've created an example plugin that can be
duplicated and used to create a new plugin. Let's do this by calling the
following from the root of the oso repository (feel free to use a name besides
`my-plugin`):

```bash
$ cp -r cloudquery/example-plugin cloudquery/my-plugin
```

## Update the `pyproject.toml` file

You'll need to update the `pyproject.toml` file within the plugin directory with
the proper naming of your new plugin and add any dependencies you may need. It's
important that you use a name that is unique to the plugin within the oso
repository.

Assuming we need the `requests` added to the dependencies. This is what your
`pyproject.toml` should look like:

```toml
[tool.poetry]
name = "my-plugin" # Update this to the plugin name
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

## Adding the plugin to the poetry configuration at the top of the repo

The oso repository is structured as a monorepo (for both node and python
projects). So in order to properly manage the repo's dependencies you'll need to
add your plugin to the monorepo at the root of the repository.

Within the `pyproject.toml` at the root of the repository, under the
`[tool.poetry.dependencies]` section, make it appear like so, with your plugin's
directory:

```toml
[tool.poetry.dependencies]
python = "^3.11"
oso-dbt = { path = "./dbt", develop = true }
example-plugin = { path = "cloudquery/example-plugin", develop = true }
my-plugin = { path = "cloudquery/my-plugin", develop = true }
```

## Installing the dependencies for the new plugin

To install the dependencies of the new plugin make sure you're in the root of
the oso repository and run the following:

```bash
$ poetry update
```

This will add the new plugin and also will add a script on the `PATH` for the
new plugin at `my_plugin` (or whatever name you used).

## Updating dependencies

Any time you update dependencies in the plugin just run:

```bash
$ poetry update
```

## Developing the plugin

As noted in a previous disclaimer, this doc isn't (_yet_) a full tutorial on
writing a CloudQuery plugin. For now, this will just get you started on the
boilerplate required to create a new one. To see the full documention use the
[CloudQuery
Docs](https://docs.cloudquery.io/docs/developers/creating-new-plugin/python-source)

## Packaging the plugin

Once you've finished developing the plugin, you'll need to package the plugin
for use. Luckily, the `oso` repository is automatically configured to handle
packaging all plugins in the `cloudquery` directory as long as they're python or
typescript plugins. So, as long as you have followed this guide the automation
in the repository will handle properly building, packaging, and publishing a
docker image for your cloudquery plugin.
