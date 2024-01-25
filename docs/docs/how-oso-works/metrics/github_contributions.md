# GitHub Code Contribution Metrics

> This document provides details on Open Source Observer's GitHub metrics. GitHub metrics are typically queried by project (eg, `uniswap`), although they can also be queried by repo in the format (eg, `repo-owner/repo-name`).

For information about GitHub data, also see: [Developers](./developers.md)

## GitHub Code Contribution Metrics

### Repositories

Total number of repositories owned by the project, excluding forks.

### Years (Project Age)

The number of years since the first commit to the first repository owned by the project.

### Commits

Number of commits made to a repository's main branch, excluding bots and commits from forked repos.

### Forks

Number of times a repository has been forked.

### Stars

Number of unique users who have starred a repository.

### Issues Opened

Number of issues opened in a repository.

### Issues Closed

Number of issues closed in a repository.

### Pull Requests (PRs) Merged

Number of pull requests merged in a repository.

### Pull Requests (PRs) Approved

Number of pull requests approved in a repository.

### Total Contributions

Number of unique individual contribution events to a repository through commits, issues, and pull requests.

### Other Activities

Other activities logged by GitHub, including removal of pull requests and issues, reopening of issues, etc can also be queried via the API, although aggregate statistics are not displayed on Open Source Observer.

## API Reference

The following event `typeId`s are relevant to gathering GitHub metrics:

```
'COMMIT_CODE': 4,
'PULL_REQUEST_CREATED': 2,
'PULL_REQUEST_MERGED': 3,
'PULL_REQUEST_CLOSED': 13,
'PULL_REQUEST_REOPENED': 15,
'PULL_REQUEST_REMOVED_FROM_PROJECT': 16,
'PULL_REQUEST_APPROVED': 17,
'ISSUE_FILED': 5,
'ISSUE_CLOSED': 6,
'ISSUE_CREATED': 18,
'ISSUE_REOPENED': 19,
'ISSUE_REMOVED_FROM_PROJECT': 20,
'STARRED': 21,
'FORKED': 23,
'STAR_AGGREGATE_STATS': 14,
'FORK_AGGREGATE_STATS': 22,
```
