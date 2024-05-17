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


RUN mkdir -p /usr/bin/app && \
    bash -c "mkdir -p /usr/bin/app/warehouse/{bq2cloudsql,oso_dagster,oso_lets_go,common}" && \
    touch /usr/bin/app/warehouse/bq2cloudsql/__init__.py && \
    touch /usr/bin/app/warehouse/bq2cloudsql/script.py && \
    touch /usr/bin/app/warehouse/oso_dagster/__init__.py && \
    touch /usr/bin/app/warehouse/oso_lets_go/__init__.py && \
    touch /usr/bin/app/warehouse/oso_lets_go/wizard.py && \
    touch /usr/bin/app/warehouse/common/__init__.py

WORKDIR /usr/bin/app
COPY pyproject.toml poetry.lock /usr/bin/app/
COPY warehouse/cloudquery-example-plugin /usr/bin/app/warehouse/cloudquery-example-plugin

# Install everything onto the system path
RUN poetry config virtualenvs.create false && \
    poetry install

RUN rm -r /usr/bin/app/warehouse 

COPY . /usr/bin/app

RUN poetry config virtualenvs.create false && \
    poetry install