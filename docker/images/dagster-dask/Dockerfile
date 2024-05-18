FROM ubuntu:jammy

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.12
RUN apt-get install -y curl && \
    curl -o get-pip.py https://bootstrap.pypa.io/get-pip.py && \
    python3.12 get-pip.py
RUN pip3.12 install poetry

ENV DAGSTER_DBT_PARSE_PROJECT_ON_LOAD=1
ENV DAGSTER_DBT_GENERATE_AND_AUTH_GCP=1

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
COPY warehouse/cloudquery-example-plugin /usr/src/app/warehouse/cloudquery-example-plugin

# Install everything onto the system path
RUN poetry config virtualenvs.create false && \
    poetry install

RUN rm -r /usr/src/app/warehouse 

COPY . /usr/src/app

RUN poetry config virtualenvs.create false && \
    poetry install

ENTRYPOINT [ "dagster", "api", "grpc", "-p", "3030"]