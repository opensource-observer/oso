---
title: Developing in the WASM Environment
sidebar_position: 1
---

In order to make wasm notebooks a possibility we utilize marimo's ability to run
inside of the browser. For OSO, we've added some special configurations that are
unique to the OSO platform. In order to support this, we created a tool that
allows us to easily test changes in the python environment that is loaded into
marimo. Additionally, it allows us to inject our own WASM controller so that we
can provide a tailored experience.

The primary tool for all of this is called `wasm-builder` and must currently be
loaded from OSO's [marimo fork](https://github.com/opensource-observer/marimo).
This is a proxy for testing the wasm version of marimo and would only be useful
in that regard. The proxy allows us the following features while testing:

- Create and serve an updated wasm compatible marimo python wheel based on
  changes in the local environment
  - By default, marimo's wasm environment links to a deployed version of
    marimo. Using this proxy allows completely localized development.
- Create an up to date pyodide lock file for the wasm frontend
  - The pyodide lock file, much like a `uv.lock` or `package-lock.json` file,
    ensures that the same versions of packages are used each time. This is
    important for stability and reproducibility. This file normally requires a
    bit of manual work to generate. The `wasm-builder` tool automatically
    regenerates this as needed as the local marimo python code is changed.
- Support developing _any_ python code for use in wasm
  - In addition to marimo's based code required to run the wasm notebook, we
    can also generate updated wheel files for any uv based python project
    (this is extensible to other package management solutions in the future).

## Prerequisites

Please ensure the following are installed:

- [pixi](https://pixi.sh)
  - Needed for the marimo code
- [docker](https://www.docker.com/)

## Starting the development environment

Since `wasm-builder` is a proxy you will also need a proxied service to be
running. That proxied service, in this case, should be the marimo frontend. To
this, first clone OSO's marimo fork:

```bash
git clone https://github.com/opensource-observer/marimo.git
cd marimo
```

In one terminal start the frontend:

```bash
pixi run hatch shell # Start a shell in the pixi environment
make fe # build the frontend
cd frontend
# Start the frontend. You will want to set PYODIDE=true so that you can force the use of the
# pyodide backend. Vite sometimes needs a bit more memory with the marimo frontend build.
# Hence the `NODE_OPTIONS` setting.
PYODIDE=true NODE_OPTIONS=--max-old-space-size=6144 pnpm vite --config oso.viteconfig.mts
```

:::Note
If you would like to remove `react-scan` from the frontend dev server you should
ensure that `NODE_ENV != "development"`. You can set this to something like
`NODE_ENV=test`
:::

The frontend listens on port 3000 by default. In another terminal, you can start
the wasm-builder proxy (this is from the root of the fork):

```bash
pixi run hatch shell # Ensure you're in the pixi environment
cd packages/wasm-builder
pnpm start
```

The server will start listening on port 6008 by default.

:::Note
If you happen to be developing, using a remote development setup you will want
to make sure you set the `PUBLIC_PACKAGES_HOST` to the correct host for your
remote setup.
:::

To access the notebook now, you can navigate to `http://localhost:6008/notebook` in your
browser. The `/notebook` endpoint is specific to OSO's wasm environment.

:::
Note: If you access the frontend without the proxy, you will not be
able to have a working wasm environment.
:::

## Setting up pyoso and oso_semantic in the development environment

As part of OSO's marimo wasm environment, we load both pyoso and oso_semantic
into the pyodide environment. It is likely that you will want to develop against
these in the wasm environment. To do so, you need to add the following to the
`.env` in the `wasm-builder`'s main directory:

```bash
OTHER_UV_PACKAGES_TO_INCLUDE='[{"name": "pyoso", "projectDir": "/path/to/pyoso", "outputDir": "/path/to/oso/dist"},{"name": "oso_semantic", "projectDir": "/path/to/oso_semantic", "outputDir": "/path/to/oso/dist"} ]'
```

You may notice that `outputDir` says `/path/to/oso/dist`. This is supposed to be
the path to where you store the `oso` monorepo and then the `/dist` subdirectory
within (which is where the built artifacts will be placed by uv).

## Manually testing the build

Inevitably, you will want to manually test the build for wasm. To do so you can
use the build scripts that we have in the marimo repository. The syntax for this
is as follows:

```bash
bash scripts/build_marimo_static_dist.sh <build-dir> <host> [<port>]
```

The `build-dir` and `host` are both required, while the `port` is optional and
defaults to `443`. As we are testing, we likely need to set both the `host` and
`port` arguments. For the host variable, you will want to ensure that it points
to the correct host your browser will be accessing when you test this. Assuming
you're developing this locally, it's likely `127.0.0.1`. For the port, choose
any port you like for this example, we will use `6008`.

In addition, we will want to ensure that the `NODE_ENV` is explicitly set to
something that is not `production`. Production builds will ignore additional uv
packages (as it's expected that we are building from things on pypi).

So finally, to run the build into a directory `.static_wasm`:

```bash
cd /path/to/marimo
pixi run hatch shell
NODE_ENV=test bash scripts/build_marimo_static_dist.sh .static_wasm 127.0.0.1 6008
```

Then to serve this, you can use a simple python server:

```bash
cd .static_wasm
python3 -m http.server 6008
```

Now you can go to your browser at http://localhost:6008/notebook.html.

:::Note
Python simple server does support reference html files without `.html`. This
would be different behavior than something deployed on our production setup.
:::
