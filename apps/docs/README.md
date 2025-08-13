# Website

This website is built using [Docusaurus](https://docusaurus.io/), a modern static website generator.

### Installation

```
$ pnpm install
```

### Local Development

```
$ pnpm start
```

This command starts a local development server and opens up a browser window. Most changes are reflected live without having to restart the server.

### Plasmic development

If you are making changes to Plasmic components,
you will need to run Plasmic sync and check the generated code in to the repository.

You can run a full build via

```
$ pnpm build:everything
```

Or you can just run the Plasmic sync via

```
# pnpm plasmic:sync
```

### Build

To just run the Docusaurus build

```
$ pnpm build
```

This command generates static content into the `build` directory and can be served using any static contents hosting service.

### Deployment

Using SSH:

```
$ USE_SSH=true pnpm run deploy
```

Not using SSH:

```
$ GIT_USER=<Your GitHub username> pnpm run deplon
n``

If you are using GitHub pages for hosting, this command is a convenient way to build the website and push to the `gh-pages` branch.
```
