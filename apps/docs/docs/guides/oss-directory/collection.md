---
title: Collection
sidebar_position: 2
---

:::info
A **collection** is a group of related open source projects in the OSS Directory. Projects may belong to multiple collections. For example, a collection may include all projects that are part of a particular ecosystem or all projects that are dependent on a given developer library.
:::

## Collection Identification

---

The `name` field is used to identify the collection. It is a unique identifier that is used to reference the collection in other parts of the directory. It should be a string that is all lowercase and contains only letters, numbers, and hyphens.

You can browse examples of collections in the [OSS Directory](https://github.com/opensource-observer/oss-directory/tree/main/data/collections).

## Display Name and Description

---

The `display_name` is a required field used to store a working name for the collection. It is case sensitive. Longer names (eg, greater than 25 chars) may sometimes be truncated in the UI or charts.

The `description` is an optional field used to store a short description of the collection. It is case sensitive. Longer descriptions (eg, greater than 100 chars) may sometimes be truncated in the UI.

## Projects

---

The `projects` field is a required field used to store an array of project names associated with the collection. Each item in the array must be a valid project `name`. If one or more project names are not valid, the collection will not be added to the directory.

You can learn more about adding and updating projects to the OSS Directory [here](./project).

## Example

---

Here is a simple example of a collection YAML file in the OSS Directory:

```yaml
name: my-collection
display_name: My Collection
projects:
  - project-name1
  - project-name2
  - project-name3
```

## Full Schema

---

You can always access the most recent version of the schema [here](https://github.com/opensource-observer/oss-directory/blob/main/src/resources/schema/collection.json).

```json
{
  "$id": "collection.json",
  "title": "Collection",
  "type": "object",
  "description": "A collection of projects",
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
    "projects": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "string"
      }
    }
  },
  "required": ["version", "name", "display_name", "projects"]
}
```

## Contributing

---

Collections are updated and added to the OSS Directory by members of the Data Collective. If you are interested in joining the Data Collective, you can apply [here](https://www.kariba.network/).
