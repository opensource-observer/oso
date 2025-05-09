ARG REPO_SHA=latest

FROM ghcr.io/opensource-observer/oso-base:${REPO_SHA}

ARG PYTHON_VERSION=3.12

WORKDIR /usr/src/app
COPY . ./

# Install everything onto the system path
RUN ln -s /usr/bin/python3.12 /usr/local/bin/python
ENV UV_PROJECT_ENVIRONMENT=/usr/local/

RUN uv sync --all-packages --locked

ENTRYPOINT  []