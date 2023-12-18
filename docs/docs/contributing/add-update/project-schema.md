---
title: Project Schema
sidebar_position: 2
---

# Project Schema

The project schema is used to store information about open source projects in the OSS Directory.

The `version` field is used to track the version of the project schema. It should be a number that is incremented by 1 for each new version of the schema. The current version of the schema is Version 3.

The `slug` field is used to identify the project. It is a unique identifier that is used to reference the project in other parts of the directory. It should be a string that is all lowercase and contains only letters, numbers, and hyphens. In most cases, we adopt the GitHub organization name as the slug (eg, `my-org`). If the project is not associated with a GitHub organization, you can use the project name followed by the repo owner as the slug, separated by hyphens (eg, `my-repo-my-org`). You can browse other examples in the [OSS Directory](https://github.com/opensource-observer/oss-directory/tree/main/data/projects).

For URL fields (eg, `github` and `npm`), the schema requires that the URL is a valid URL and that the URL is unique within the array. You can view the schema for the URL field [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/url.json).

For `blockchain` fields, the schema requires that the address is a valid address and that the address is unique within the array. Read more about the blockchain address schema [here](./blockchain-address-schema).

## Full Schema

You can always access the most recent version of the schema [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/project.json).

```
{
  "$id": "project.json",
  "title": "Project",
  "type": "object",
  "description": "A project is a collection of artifacts",
  "properties": {
    "version": {
      "type": "number"
    },
    "slug": {
      "type": "string"
    },
    "name": {
      "type": "string"
    },
    "github": {
      "type": "array",
      "items": {
        "$ref": "url.json#"
      }
    },
    "npm": {
      "type": "array",
      "items": {
        "$ref": "url.json#"
      }
    },
    "blockchain": {
      "type": "array",
      "items": {
        "$ref": "blockchain-address.json#"
      }
    }
  },
  "required": ["version", "slug", "name"]
}

```
