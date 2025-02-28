---
title: Supabase
sidebar_position: 4
---

## Setup

- Database >> Extensions
  - Enable the "plpgsql", "plv8" and "pgjwt" extensions
- Authentication >> Providers
  - Turn on the Google provider
- Authentication >> URL Configuration
  - Add allowed redirect URIs
    - `https://www.opensource.observer/**`
    - `http://localhost:3000/**`
- Settings >> Authentication
  - Turn on "Allow new users to sign up"

Run the Supabase migrations to create the tables and functions required for the OSO project.

```bash
cd frontend/
pnpm supabase db push
```

- Authentication >> Hooks
  - Enable the "hasura_token_hook" hook under the "public" schema

## Migrations

For updating the database schema or functions, make sure to put it in a migration.

```bash
pnpm supabase migration new
```

After editing the migration, you can apply it to production with:

```bash
pnpm supabase db push
```

If you need to see which migrations have been applied, you can run:

```bash
pnpm migration list
```

For more details, check out the
[Supabase docs](https://supabase.com/docs/reference/cli/supabase-migration).
