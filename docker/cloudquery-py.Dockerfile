ARG BASE_IMAGE=ghcr.io/opensource-observer/cloudquery-py-base:latest

FROM ${BASE_IMAGE}

ARG PLUGIN_NAME

ENTRYPOINT [ "${PLUGIN_NAME}" ]