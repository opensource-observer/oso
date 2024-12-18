---
title: Schema Updates
sidebar_position: 6
---

:::info
Every schema in the OSS Directory has a `version` field. This field is used to track the version of the schema. It should be a number that is incremented by 1 for each new version of the schema.
:::

:::tip
The current version of the OSS Directory schema is **Version 7**.
:::

All files under `./data` must conform to schemas defined in `./src/resources/schema`.
Our continuous integration system will reject any pull requests that do not validate against the schema.

If you want to change the schema, you'll need to write a migration:

1. Update the schema in `src/resources/schema/`
2. Add a [version]-[desc].ts file to the `src/migrations/` folder, exporting functions that migrate each file type.
3. Add the migration functions to the MIGRATIONS array in `src/migrations/index.ts`.
4. You can run the migration by running `pnpm migrate`
5. Make sure to commit and submit a pull request with all of the resulting changes. We will not accept any PRs where the data does not conform to the schemas.

The framework will run migrations in sequence, so you are guaranteed that your data is valid as of the previous version.
Note: we only currently support migrating in one direction (and not reverting)

Whenever a new schema version is released, the previous version will be deprecated and all data will be migrated to the new version. This ensures that the OSS Directory is always using the latest version of the schema.
