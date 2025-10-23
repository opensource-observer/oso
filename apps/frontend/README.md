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

In order to properly install `supabase`, you'll need to explicitly approve post-installation scripts:

```bash
pnpm approve-builds
```

## Log into Supabase and start the dev server

```bash
pnpm supabase login
pnpm supabase start
```

Remember to update your `.env.local` with the generated local Supabase settings.
We recommend that you **DO NOT** use the production Supabase server locally,
as tests and migrations can be dangerous/destructive.

## Run the dev server

To run the dev server, which will also automatically watch for changes from Plasmic and the GraphQL schema:

```bash
pnpm dev
```

Remember to set `preview: true` in `plasmic-init.ts` if you want to see unpublished changes from Plasmic Studio without publishing the Plasmic project.

## Build

To create a production build (code+build):

```bash
pnpm build:prod
```

You can also run codegen and the Next.js build separately:

```bash
pnpm codegen
pnpm build:next
```

The resulting static site can be found in `./build/`.
You can serve built files with:

```bash
pnpm start
```

## Lint and test

```bash
pnpm lint
pnpm test
```

### Codegen

:::tip
You can run `pnpm codegen` to run all of these codegen stages at once.
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

We also codegen TypeScript types for all Supabase queries.
If you make changes to the Supabase schema, make sure to run:

```bash
pnpm supabase:gentypes
```

## Deploy

Currently, all deployments are automatically handled by Vercel's GitHub app.
