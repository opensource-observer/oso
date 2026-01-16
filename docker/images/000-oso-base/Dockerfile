FROM ghcr.io/opensource-observer/oso-public-vars:latest AS public_vars


FROM python:3.12-slim-bookworm

ARG GCLOUD_VERSION=503.0.0
ARG PYTHON_VERSION=3.12
ARG PYTHON_PACKAGE=python3.12
ARG REPO_SHA=
ARG ORDERED_TAG=

ENV DEBIAN_FRONTEND=noninteractive
ENV DBUS_SESSION_BUS_ADDRESS=""

RUN apt-get update && \
    apt-get install -y software-properties-common && \
    apt-get install -y curl git && \
    pip install uv && \
    curl -o gcloud.tar.gz https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_VERSION}-linux-x86_64.tar.gz && \
    tar xvf gcloud.tar.gz && \
    bash ./google-cloud-sdk/install.sh && \
    rm gcloud.tar.gz && true && \
    echo "${ORDERED_TAG}" > /oso.ordered_tag.txt && \
    echo "${REPO_SHA}" > /oso.repo_sha.txt
ENV PATH $PATH:/google-cloud-sdk/bin

COPY --from=public_vars ./public/vars.env /public-vars.env

ENTRYPOINT  ["/bin/bash"]