FROM ghcr.io/opensource-observer/oso-public-vars:latest AS public_vars


FROM ubuntu:jammy

ARG GCLOUD_VERSION=478.0.0
ARG PYTHON_VERSION=3.12
ARG PYTHON_PACKAGE=python3.12

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y ${PYTHON_PACKAGE} && \
    apt-get install -y curl git && \
    curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python${PYTHON_VERSION} get-pip.py && \
    pip${PYTHON_VERSION} install poetry && \
    curl -o gcloud.tar.gz https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_VERSION}-linux-x86_64.tar.gz && \
    tar xvf gcloud.tar.gz && \
    bash ./google-cloud-sdk/install.sh && \
    rm gcloud.tar.gz && true
ENV PATH $PATH:/google-cloud-sdk/bin

RUN mkdir -p /usr/src/app && \
    bash -c "mkdir -p /usr/src/app/warehouse/{bq2cloudsql,oso_dagster,oso_lets_go,common}" && \
    touch /usr/src/app/warehouse/bq2cloudsql/__init__.py && \
    touch /usr/src/app/warehouse/bq2cloudsql/script.py && \
    touch /usr/src/app/warehouse/oso_dagster/__init__.py && \
    touch /usr/src/app/warehouse/oso_lets_go/__init__.py && \
    touch /usr/src/app/warehouse/oso_lets_go/wizard.py && \
    touch /usr/src/app/warehouse/common/__init__.py

WORKDIR /usr/src/app
COPY pyproject.toml poetry.lock /usr/src/app/

# Install everything onto the system path
RUN poetry config virtualenvs.create false && \
    poetry install

RUN rm -r /usr/src/app/warehouse 

COPY . /usr/src/app

RUN poetry config virtualenvs.create false && \
    poetry install

ENV DAGSTER_DBT_TARGET_BASE_DIR=/dbt_targets

COPY --from=public_vars ./public/vars.env /usr/src/app/vars.env
RUN mkdir -p ${DAGSTER_DBT_TARGET_BASE_DIR} && \
    python${PYTHON_VERSION} -m oso_dagster.compile --additional-vars /usr/src/app/vars.env

ENTRYPOINT  []