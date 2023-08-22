# This is a hack to allow for persistent caching
ARG BASE_IMAGE=scratch
FROM ${BASE_IMAGE}

ARG CREATION_DATE=

COPY ./cache/ /cache/

LABEL observer.opensource.cache_creation_date=${CREATION_DATE}
