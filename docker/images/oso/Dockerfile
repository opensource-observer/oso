ARG REPO_SHA=latest

FROM ghcr.io/opensource-observer/oso-base:${REPO_SHA}

ARG PYTHON_VERSION=3.12

RUN mkdir -p /usr/src/app && \
    bash -c "mkdir -p /usr/src/app/warehouse/{bq2cloudsql,oso_dagster,oso_lets_go,common,metrics_tools}" && \
    bash -c "mkdir -p /usr/src/app/ops/opsscripts" && \
    touch /usr/src/app/README.md && \
    touch /usr/src/app/warehouse/bq2cloudsql/__init__.py && \
    touch /usr/src/app/warehouse/bq2cloudsql/script.py && \
    touch /usr/src/app/warehouse/oso_dagster/__init__.py && \
    touch /usr/src/app/warehouse/oso_lets_go/__init__.py && \
    touch /usr/src/app/warehouse/oso_lets_go/wizard.py && \
    touch /usr/src/app/warehouse/metrics_tools/__init__.py && \
    touch /usr/src/app/warehouse/common/__init__.py && \
    touch /usr/src/app/ops/opsscripts/__init__.py

WORKDIR /usr/src/app
COPY pyproject.toml poetry.lock /usr/src/app/

# Install everything onto the system path
RUN poetry config virtualenvs.create false && \
    poetry install

RUN rm -r /usr/src/app/warehouse && \
    rm -r /usr/src/app/ops

COPY . /usr/src/app

ENV DAGSTER_DBT_TARGET_BASE_DIR=/dbt_targets

RUN mkdir -p ${DAGSTER_DBT_TARGET_BASE_DIR} && \
    python${PYTHON_VERSION} -m oso_dagster.compile --additional-vars /public-vars.env

ENTRYPOINT  []