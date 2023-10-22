# GitHub Contributor Metrics

> This document outlines how we define and categorize developers, maintainers, and other types of contributors, and how we assign activity levels to them based on their contributions. GitHub metrics are typically queried by project (eg, `uniswap`), although they can also be queried by repo in the format (eg, `repo-owner/repo-name`).

For information about GitHub data, also see: [Github Contributions](./github_contributions.md)

## GitHub Contributor Metrics

> Note: most of the metrics below are defined in the context of a "contributor" (the most general category of people working on a project), but definitions like "full-time" / "part-time" and "new" / "inactive" are also applicable to "developers" and "maintainers".

### Contributors
Count of individual users (excluding bot accounts) who have contributed to a repository.

### Developers
Count of contributors that have made code commits.

### Maintainers
Count of contributors that have merged pull requests or closed issues.

### Monthly Active Contributors
Count of contributors that have made at least one contribution over a 30-day period.

### Full-Time Contributors
Count of monthly active contributors that have made contributions on 10 or more days over a 30-day period.

### Part-Time Contributors
Count of monthly active contributors that have made contributions on fewer than 10 days over a 30-day period.

### New Contributors
Count of contributors who made their first contribution in the last 90 days.

### Inactive Contributors
Count of past contributors who have not made any contributions in the last 90 days.

### Contributor Churn Rate
The proportion of inactive contributors to the total number of contributors, excluding new contributors.

### Ecosystem Users
Count of contributors that have also contributed to at least two other projects in the same collection.

### Active Ecosystem Users
Count of active contributors that are also active in at least two other projects in the same collection.

## API Reference

The following event `typeId`s are relevant to calculating contributor metrics:
```
'COMMIT_CODE': 4,
'PULL_REQUEST_CREATED': 2,
'PULL_REQUEST_MERGED': 3,
'PULL_REQUEST_APPROVED': 17,
'ISSUE_CLOSED': 6,
'ISSUE_CREATED': 18,
```