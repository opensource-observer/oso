---
title: Project
sidebar_position: 3
---

:::info
A **project** is a group of artifacts owned by a project in the OSS Directory. For example, a project may include a GitHub organization, a blockchain address, and a NPM package. An artifact can only belong to one project.
:::

## Project Identification

---

The `name` field is used to identify the project. It is a unique identifier that is used to reference the project in other parts of the directory. It should be a string that is all lowercase and contains only letters, numbers, and hyphens. In most cases, we adopt the GitHub organization name as the `name` (eg, `my-org`). If the project is not associated with a GitHub organization, you can use the project name followed by the repo owner as the `name`, separated by hyphens (eg, `my-repo-my-org`).

You can browse other examples in the [OSS Directory](https://github.com/opensource-observer/oss-directory/tree/main/data/projects).

## Display Name and Description

---

The `display_name` is a required field used to store a working name for the project. It is case sensitive. Longer names (eg, greater than 25 chars) may sometimes be truncated in the UI or charts.

The `description` is an optional field used to store a short description of the project. It is case sensitive. Longer descriptions (eg, greater than 100 chars) may sometimes be truncated in the UI.

## Artifacts

---

The `github`, `npm`, and `blockchain` fields are used to store arrays of artifacts associated with the project. Each item in an artifact array must contain either a `url` field that is a valid URL or an `address` representing a public key address on a blockchain. More information about artifact schemas can be found [here](./artifact).

As of Version 5, you can also include `websites` as artifacts. This field is used to store an array of URLs that are associated with the project. Each item in the array must contain a `url` field that is a valid URL.

## Example

---

Here is a simple example of a project YAML file in the OSS Directory:

```yaml
name: my-project
display_name: My Project
github:
  - url: https://github.com/my-project
websites:
  - url: https://my-project.com
blockchain:
  - address: "0x87feed6162cb7dfe6b62f64366742349bf4d1b05"
    networks:
      - mainnet
      - optimism
    tags:
      - eoa
      - wallet
```

## Full Schema

---

You can always access the most recent version of the schema [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/project.json).

```json
{
  "$id": "project.json",
  "title": "Project",
  "type": "object",
  "description": "A project is a collection of artifacts",
  "properties": {
    "version": {
      "type": "number"
    },
    "name": {
      "type": "string"
    },
    "display_name": {
      "type": "string"
    },
    "websites": {
      "type": "array",
      "items": {
        "$ref": "url.json#"
      }
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
  "required": ["version", "name", "display_name"]
}
```

## Contributing

---

Projects are updated and added to the OSS Directory by members of the Data Collective. To learn more about contributing to the OSS Directory, start [here](../../projects). If you are interested in joining the Data Collective, you can apply [here](https://www.kariba.network).
