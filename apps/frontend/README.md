# OSO frontend app

This frontend is configured for the Next.js app router.
By default, it makes use of SSR and RSC to generate pages on demand for data found in the database.
You can also configure this for a static site build.

## Configure

Make sure you have a `.env.local` properly populated with all configuration variables.
These will be required to build.

You can set `STATIC_EXPORT=true` if you want a static site built.

## Install dependencies

We typically use `pnpm` for package management.

```bash
pnpm install
```

## Run the dev server

To run the dev server, which will also automatically watch for changes from Plasmic and the GraphQL schema:

```bash
pnpm dev
```

Remember to set `preview: true` in `plasmic-init.ts` if you want to see unpublished changes from Plasmic Studio without publishing the Plasmic project.

## Build, lint, test

To build, lint, and test, run the following

```bash
pnpm build
pnpm lint
pnpm test
```

The resulting static site can be found in `./build/`.
You can serve built files with:

```bash
pnpm start
```

### GraphQL queries

:::tip
The default `pnpm build` will handle all of this.
:::

We self-host an Apollo gateway in Next.js/Vercel, which routes all requests to Hasura.
If the Hasura schema changes, we need to regenerate the supergraph schema for Apollo:

```bash
pnpm graphql:schema
```

We codegen TypeScript types for all GraphQL queries.
If you make changes to the GraphQL schema (e.g. on Hasura), make sure to run:

```bash
pnpm graphql:codegen
```

## Deploy

Currently, all deployments are automatically handled by Vercel's GitHub app.

## Supabase Migrations

For updating the database schema or functions, make sure to put it in a migration.

```bash
npx supabase migration new
```

After editing the migration, you can apply it to production with:

```bash
npx supabase db push
```

If you need to see which migrations have been applied, you can run:

```bash
pnpm migration list
```

Then, to codegen all Supabase schemas as TypeScript types:

```bash
pnpm supabase:gentypes
```

For more details, check out the
[Supabase docs](https://supabase.com/docs/reference/cli/supabase-migration).
