# OSO CloudQuery Plugins

[CloudQuery](https://cloudquery.io) is used to integrate external data sources
into the Open Source Observer platform. At this time we are limiting the
cloudquery plugins in the OSO repository to Python or Typescript. This page will
go over writing a plugin with python, which is our suggested plugin language.

## Getting Started

Disclaimer: _We consider this a basic tutorial for creating a CloudQuery Plugin,
you can use the [CloudQuery Docs](https://docs.cloudquery.io/docs) if you'd like
to learn more._

Before we begin you'll need at least the following installed:

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

## Starting a new plugin

To make this simple we've created an example plugin that can be duplicated and
used to create a new plugin.

## Adding the plugin to the poetry configuration at the top of the repo

## Packaging the plugin

As long as you have followed this guide the automation in the repository will
handle properly building, packaging, and publishing a docker image for your
cloudquery plugin.
