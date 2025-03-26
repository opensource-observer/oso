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

We codegen types for all GraphQL queries. If you make changes to the GraphQL schema (e.g. on Hasura), make sure to run

```bash
pnpm graphql:compile
```

## Deploy

Currently, all deployments are automatically handled by Vercel's GitHub app.

## Architecture

More coming...

All data is accessed through a Hasura GraphQL engine. In the future, we may be able to run this on Cloudflare workers/pages in the edge runtime due to this architecture decision.
