# you've changed bro

A toolset for handling changes in your polyglot monorepo. It's main use is to
deteremine workspace boundaries and the dependency graph of the workspaces.

## Features

- Intentionally built for polyglot monorepos
- Ensures commits are separated by workspace
- Workspaces are separated based on various workspace configuration for supported languages.
- Can trigger any command on changes to a workspace

## Tools

### `ycb commitlint`

A tool used for githooks to ensure that commits are separated by workspace.
Based on workspace boundaries, this ensures that the git commits are split based
on workspace boundaries and automatically labeled. This _assumes_ that
conventional commits are used.

### `ycb workspaces`

A set of commands to manage and view workspaces

### `ycb workspaces list`

Lists all workspaces for a project.

### `ycb workspaces <workspace> changelog`

Generates a changelog for the given workspace.

## Contextual Configuration

`ycb` uses contextual configuration for each workspace. Top level project
configuration is handled by a `ycb.json`.

The configuration options:

```json
{
  "discover": ["uv", "pnpm"],
  "workspaces": {} // any explicit workspaces you'd like to explicitly list
}
```
