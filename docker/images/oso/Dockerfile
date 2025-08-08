ARG REPO_SHA=latest

FROM ghcr.io/opensource-observer/oso-base:${REPO_SHA}

ARG PYTHON_VERSION=3.12

WORKDIR /usr/src/app
COPY . ./

# Install everything onto the system path
RUN ln -s /usr/bin/python3.12 /usr/local/bin/python
ENV UV_PROJECT_ENVIRONMENT=/usr/local/

RUN uv sync --all-packages --locked

# Build the dagster for production
ENV DAGSTER_ASSET_CACHE_DIR=/dagster_assets_cache
ENV DAGSTER_ASSET_CACHE_ENABLED=1
ENV DAGSTER_SQLMESH_GATEWAY=trino
ENV GOOGLE_PROJECT_ID=opensource-observer
RUN uv run oso_dagster build

ENTRYPOINT  []
