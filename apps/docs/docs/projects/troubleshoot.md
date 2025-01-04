---
title: Troubleshoot Data Issues
sidebar_position: 5
---

:::tip
If you can't find an answer to your question here, please jump into our [Discord](https://www.opensource.observer/discord) and ask in the #help channel. If you spot a bug or have a feature request, please [open an issue](https://github.com/opensource-observer/oso/issues).
:::

## I Don't See My Project Data

Our full indexer currently runs weekly on Sundays. Therefore, it may take up to a week for your project data to be indexed. Backfills are run periodically to ensure that all data is indexed. If you don't see any historic event data for your project, than the most likely reason is that the backfill has not yet been run.

If it's been more than a week and you still don't see your project data, there are a few things you can check:

- Confirm that your project is correctly listed in the [oss-directory](https://github.com/opensource-observer/oss-directory).
- Check if we've pulled the data from oss-directory recently. Our pipeline is public and runs weekly. You can see the latest run [here](https://dagster.opensource.observer/assets/ossd).
- Check if the full pipeline has run or encountered an error. You can see the status of the projects_v1 model [here](https://dagster.opensource.observer/assets/dbt/production/projects_v1). If the latest run has failed, you will see a red X under "Latest materialization" at the top of the page.

If all of these checks pass, then send us a message in [Discord](https://www.opensource.observer/discord) and we'll take a look.

## My Project Started Earlier Than Your Data Shows

OSO does not index GitHub event data directly; we use a public dataset of GitHub events from [GitHub Archive](https://www.githubarchive.org/) starting from 2015-01-01. If your project started before then, those events won't be captured in OSO.

If your project began as part of a private repository, then we won't have event data until the repository was made public.

If your project was initially created in another Git hosting service (eg, GitLab, Bitbucket, etc), then we won't have event data until the project was moved to GitHub.

If your project has had multiple owners and/or aliases, then there could be an edge case in one of our models or in gharchive. You can add the historic aliases to the project file as additional `github` URLs. If this doesn't resolve the issue or you have some other bizarre edge case, please reach out to us in [Discord](https://www.opensource.observer/discord) and we'll take a look.

## Someeone Else Claimed One of My Project Artifacts

Oh no! We're sorry about that. Please [open a pull request in oss-directory](https://github.com/opensource-observer/oss-directory/pulls) and we'll review it.

## I Need Help Adding My Project

Here's a more detailed set of instructions for first-time contributors.

### 1. Fork oss-directory

- Navigate to the [oss-directory](https://github.com/opensource-observer/oss-directory) repo.

- Click the "Fork" button in the upper right corner of this page. This will create a copy of the repository in your GitHub account. It's best practice to keep the same repository name, but you can change it if you want.

:::tip
If you run into issues, check out [GitHub's instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) for forking an open source software repository.
:::

### 2. Locate or create a new project file

- Every project file is a `.yaml` file under `./data/projects/` that looks like this:

  ```yaml
  version:
  name:
  display_name:
  github:
    - url:
  ```

- The directory is organized by the first letter of the project name. For example, if the project name is `my-project`, you can find it under `./data/projects/m/my-project.yaml`.
- Our project names and filenames are derived from a project's GitHub organization or repository name. Therefore, the easiest way to see if a project already exists in our directory is to search for its GitHub organization name. For example, if you wanted to see if we are indexing repos that belong to https://github.com/opensource-observer, then you would search for `opensource-observer` and you would discover a project page at `./data/projects/o/opensource-observer.yaml`.
- If the project doesn't exist, you can create a new `.yaml` file under `./data/projects/` In most cases, you should simply use the GitHub organization name (eg, `my-new-org`) as the name and filename (eg, `./data/projectsm/my-new-org.yaml`).
- If the project is not associated with a GitHub organization, you can use the project name followed by the repo owner as the name, separated by hyphens (eg, `my-repo-my-org`), and the same convention for the filename (eg, `./data/projects/m/my-repo-my-org.yaml`).
- Initialize the new project with the following fields:
  - `version`: The version of the schema you are using. The latest version is Version 7. You can learn more about the schema [here](../guides/oss-directory/schema-updates).
  - `name`: The unique identifier for the project. See [Give Your Project a Unique `name` Slug](./index.md#give-your-project-a-unique-name-slug) for more information.
  - `display_name`: The name of the project.
  - `github`: The GitHub URL of the project. This is a list of URLs, as a project can have multiple GitHub URLs. In most cases, the first and only URL will be the main GitHub organization URL. You don't need to include all the repositories that belong to the organization, as we will automatically index all of them.

### 3. Link artifacts to the project

- Add artifacts to the project file. Artifacts are the different types of data that we index for a project. You can find the list of artifacts in the [schema](../guides/oss-directory/artifact). Here's an example of a project file with artifacts:

  ```yaml
  version:
  name:
  display_name:
  github:
    - url:
    - url:
  npm:
    - url:
    - url:
  blockchain:
    - address:
      tags:
        -
      networks:
        -
  ```

- Here's an example of a project `.yaml` file:

  ```yaml
  version: 7 # Ensure this is the latest version
  name: opensource-observer
  display_name: Open Source Observer
  github:
  - url: https://github.com/opensource-observer
  npm:
  - url: https://www.npmjs.com/package/oss-directory
  blockchain:
  - address: "0x87fEEd6162CB7dFe6B62F64366742349bF4D1B05"
      networks:
      - any_evm
      tags:
      - eoa
      - wallet
  - address: "0xc5bfce27e0e7a7d7731bc23b92ebc62b9ed63b83"
      networks:
      - optimism
      tags:
      - safe
      - wallet
  - address: "0x5cBd6362e6F222D2A0Feb89f32566ebd27091B98"
      networks:
      - arbitrum_one
      tags:
      - safe
      - wallet
  ```

:::info
Some projects may own a lot of blockchain addresses. The most important addresses to include in your PR are deployers and wallets. We use deployers to trace all contracts deployed by a project, and wallets to trace all transactions made by a project. If you are unsure about which addresses to include, you can ask in the PR thread.
:::

### 4. Submit a pull request from your fork to our repository

- Save your changes and open a pull request from your fork to [oss-directory](https://github.com/opensource-observer/oss-directory).
- If you are adding multiple new projects, you can include them all in the same pull request, but please provide some comments to help us understand your changes.
- Opening the pull request will trigger automated validation of the artifacts you added. If there are any issues or duplicates found, the pull request will be rejected and you will be notified in the pull request thread.
- Your submission will be reviewed by a maintainer before approving the pull request. If there are any issues, you will be notified in the pull request thread.
- Your submission will be merged once it is approved by a maintainer.
- Once the pull request is merged successfully, your project will be added to the indexing queue for inclusion in all subsequent data updates.

:::tip
If you run into issues, check out [GitHub's instructions](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork) for creating a pull request from a fork.
:::

### 5. Monitor indexing status of your project data

Once your pull request is merged, you can check whether your project data has been indexed by querying [our GraphQL API](https://www.opensource.observer/graphql). Here's an example query to see that the _artifact_ `github.com/opensource-observer/oso` has been indexed:

```graphql
query findProject {
  oso_artifactsByProjectV1(
    where: {
      artifactSource: { _eq: "GITHUB" }
      artifactNamespace: { _eq: "opensource-observer" }
      artifactName: { _eq: "oso" }
    }
  ) {
    projectName
  }
}
```

Note that our full indexer currently runs weekly on Sundays. Therefore, it may take up to a week for your project data to be indexed. Backfills are run periodically to ensure that all data is indexed. If you don't see any historic event data for your project, than the most likely reason is that the backfill has not yet been run.
