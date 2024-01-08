---
title: Schema Updates
sidebar_position: 9
---

:::tip
The current version of the OSS Directory schema is **Version 3**.
:::

Every schema in the OSS Directory has a `version` field. This field is used to track the version of the schema. It should be a number that is incremented by 1 for each new version of the schema.

Whenever a new schema version is released, the previous version will be deprecated and all data will be migrated to the new version. This ensures that the OSS Directory is always using the latest version of the schema.
