FROM ghcr.io/opensource-observer/oso-public-vars:latest AS public_vars


FROM ubuntu:jammy

ARG GCLOUD_VERSION=503.0.0
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
    pip${PYTHON_VERSION} install uv && \
    curl -o gcloud.tar.gz https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-cli-${GCLOUD_VERSION}-linux-x86_64.tar.gz && \
    tar xvf gcloud.tar.gz && \
    bash ./google-cloud-sdk/install.sh && \
    rm gcloud.tar.gz && true
ENV PATH $PATH:/google-cloud-sdk/bin

COPY --from=public_vars ./public/vars.env /public-vars.env

ENTRYPOINT  ["/bin/bash"]