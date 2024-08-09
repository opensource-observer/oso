---
title: Fetch Project Info
sidebar_position: 11
---

:::info
[oss-directory](https://github.com/opensource-observer/oss-directory) contains structured data on as many open source projects as possible, enumerating all artifacts related to the project, from source code repositories to published packages and deployments. You can get the data via our npm library, python package, or downloading the data directly from GitHub.
:::

## Directory Structure

The OSS Directory is organized into two main folders:

- `./data/projects` - each file represents a single open source project and contains all of the artifacts for that project.
  - See `./src/resources/schema/project.json` for the expected JSON schema
  - Files should be named by the project `name`
  - A project's `name` must be globally unique. If there is a conflict in chosen `name`, we will give priority to the project that has the associated GitHub organization
  - In most cases, we adopt the GitHub organization name as the `name`. If the project is not associated with a GitHub organization, you try to use the project name followed by the repo owner as the `name`.
- `./data/collections` - each file represents a collection of projects that have some collective meaning (e.g. all projects in an ecosystem).
  - See `./src/resources/schema/collection.json` for the expected JSON schema
  - Collections are identified by their unique `name`

## Using as a library

We have also published this repository as a library that you can use in your own projects. This is useful if you want to build a tool that uses the data in this repository or perform your own custom analysis.

We have libraries for JavaScript and Python. We don't store the entire dataset with the package. Under the hood, this will clone the repository into a temporary directory, read all the data files, validate the schema, and return the objects. This way, you know you're getting the latest data, even if the package hasn't been updated in a while.

_Note: These do not work in a browser-environment_

### JavaScript library

[npm page](https://www.npmjs.com/package/oss-directory)

#### Installation

Install the library

```bash
npm install oss-directory
# OR yarn add oss-directory
# OR pnpm add oss-directory
```

#### Fetch all of the data

You can fetch all of the data in this repo with the following:

```js
import { Project, Collection, fetchData } from "oss-directory";

const data = await fetchData();
const projects: Project[] = data.projects;
const collections: Collection[] = data.collections;
```

#### Utility functions

We also include functions for casting and validating data:

- `validateProject`
- `validateCollection`
- `safeCastProject`
- `safeCastCollection`

### Python library

[PyPI page](https://pypi.org/project/oss-directory/)

#### Installation

Install the library

```bash
pip install oss-directory
# OR poetry add oss-directory
```

#### Fetch all of the data

You can fetch all of the data in this repo with the following:

```python
from ossdirectory import fetch_data
from ossdirectory.fetch import OSSDirectory

data: OSSDirectory = fetch_data()
projects: List[dict] = data.projects;
collections: List[dict] = data.collections;
```

## Direct Download from GitHub

All of the data is accessible from directly GitHub. You can download
[oss-directory](https://github.com/opensource-observer/oss-directory)
directly from GitHub.

Or, clone the repository from the command line:

```bash
$ git clone https://github.com/opensource-observer/oss-directory.git
```

Feel free to use the data in your own projects!
