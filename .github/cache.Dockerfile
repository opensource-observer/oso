# This is a hack to allow for persistent caching
ARG BASE_IMAGE=scratch
ARG CACHE_DIR_NAME=cache
FROM ${BASE_IMAGE}

ARG CREATION_DATE=

COPY ./${CACHE_DIR_NAME}/ /cache/

LABEL observer.opensource.cache_creation_date=${CREATION_DATE}
