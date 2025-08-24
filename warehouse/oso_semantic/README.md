# OSO-Semantic Query Layer

## Manually testing with pyodide

We need to add pyodide to CI, but for now to manually run tests do the following:

### Get current pyodide version

You will need to do this from the oso_semantic directory.

```bash
PYODIDE_EMSCRIPTEN_VERSION=$(pyodide config get emscripten_version)
```

### Install emscripten

Choose a place to store the code and git clone `emsdk`:

```bash
cd some/base/directory
git clone https://github.com/emscripten-core/emsdk
cd emsdk

./emsdk install ${PYODIDE_EMSCRIPTEN_VERSION}
./emsdk activate ${PYODIDE_EMSCRIPTEN_VERSION}
source emsdk_env.sh
```

### Build pyodide wheel

Now go back to the `oso_semantic` directory

```bash
cd oso/warehouse/oso_semantic
uv run pyodide build
```

This will generate a `.whl` file in `dist`

### Download pyodide version

Download the recent pyodide version (at the time of writing is 0.27.2):

```bash
cd dist/
wget https://github.com/pyodide/pyodide/releases/download/0.27.2/pyodide-0.27.2.tar.bz2
tar xjf pyodide-0.27.2.tar.bz2
```

This will now have generated a `dist/pyodide` directory.

### Run pytest

```bash
uv run pytest --run-in-pyodide . --runtime node --dist-dir=./dist
```
