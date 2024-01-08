# Github Resolve Repos

Resolves github urls into a stream of repositories. These URLs could either
describe a github org, user, or a single repo. If the URLs are users or
organizations, then all of the public repos for that entity will be discovered.
If the url is a single repo, only that repo will be returned.

## Input

- `github_token` - The github personal access token that needs public repository
  access.
