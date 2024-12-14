ARG REPO_SHA=latest

FROM ghcr.io/opensource-observer/oso-base:${REPO_SHA}

ARG PYTHON_VERSION=3.12

RUN apt-get update \
    && apt-get install -y vim curl git htop tmux postgresql-client && \
    curl -sL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh && \
    bash nodesource_setup.sh && \
    mkdir -p /usr/src/app && \
    apt-get install nodejs && \
    npm install -g pnpm 

COPY ./docker/images/oso-debug/build.sh /build.sh
RUN chmod +x /build.sh

# A docker image for debugging
ENTRYPOINT ["/bin/bash"]
CMD ["/build.sh"]