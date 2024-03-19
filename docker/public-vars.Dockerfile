ARG BASE_IMAGE=scratch
FROM ${BASE_IMAGE}

ARG SHA=

COPY ./public/ /public/

LABEL observer.opensource.sha=${SHA}
