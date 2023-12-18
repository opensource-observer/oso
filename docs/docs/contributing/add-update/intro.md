---
title: Adding & Updating Projects
sidebar_position: 1
---

# How to Add or Update Project Information

A **Project** on OSS Directory is a collection of **artifacts** that are associated with a single open source project. Each project has a unique `slug` that is used to identify the project in other parts of the directory.

The best way to contribute information about projects is by submitting a PR directly to [OSS Directory](https://github.com/opensource-observer/oss-directory). You can update any .yaml file under ./data/ or submit a new one.

Here's an example of a project .yaml file:

```
version: 3
slug: opensource-observer
name: Open Source Observer
github:
  - url: https://github.com/opensource-observer
npm:
  - url: https://www.npmjs.com/package/oss-directory
blockchain:
  - address: "0x87fEEd6162CB7dFe6B62F64366742349bF4D1B05"
    tags:
      - eoa
    networks:
      - optimism
      - mainnet
  - address: "0xc5bfce27e0e7a7d7731bc23b92ebc62b9ed63b83"
    networks:
      - optimism
    tags:
      - safe
      - wallet
  - address: "0x5cBd6362e6F222D2A0Feb89f32566ebd27091B98"
    networks:
      - arbitrum
    tags:
      - safe
      - wallet
```

## Detailed Instructions

### 1. Fork this repository

- Go to the [OSS Directory](https://github.com/opensource-observer/oss-directory).

- Click the "Fork" button in the upper right corner of this page. This will create a copy of the repository in your GitHub account.

- If you run into issues, check out [GitHub's instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) for forking an open source software repository.

### 2. Add or update the project information in the corresponding .yaml file under ./data/

- Check if the project you want to add/update is already in the directory. You can search for the project name in the search bar on the top of the page. The directory is organized by the first letter of the project name. For example, if the project name is `my-project`, you can find it under `./data/m/my-project.yaml`.
- If it is, you can update the corresponding .yaml file under ./data/.
- If not, you can create a new .yaml file under ./data/ and add the project information. Please make sure to include a unique slug to identify the project and at least one GitHub url. In most cases, we adopt the GitHub organization name as the slug (eg, `my-org`). If the project is not associated with a GitHub organization, you can use the project name followed by the repo owner as the slug, separated by hyphens (eg, `my-repo-my-org`).

### 3. Validate that your entry conforms to the schema and the registry rules

- The latest version of the schema is Version 3. You can learn more about the schema [here](./project-schema).
- Entries that contain duplicate artifacts or that do not conform to the schema will be rejected.

### 4. Open a pull request from your fork to this repository

- Your submission will be reviewed by a maintainer before approving the pull request. If there are any issues, you will be notified in the pull request thread.
- Your submission will be merged once it is approved by a maintainer.
- The maintainer will also add the project slug to any relevant collections. You can find the collections under ./collections/.

- Once your pull request is merged, your project will be added to the data queue for inclusing in the next data update.
