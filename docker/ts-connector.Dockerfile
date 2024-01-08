FROM node:18 as build

RUN npm install -g pnpm

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN pnpm install && pnpm build:connectors

FROM node:18 

ARG SOURCE_DIR

RUN mkdir -p /usr/src/app/${SOURCE_DIR}
COPY --from=build /usr/src/app/${SOURCE_DIR} /usr/src/app/${SOURCE_DIR}
COPY --from=build /usr/src/app/node_modules /usr/src/app/node_modules
ENV CONNECTOR_DIR=${SOURCE_DIR}
COPY <<EOF /entrypoint.sh
#!/bin/bash
set -euxo pipefail

node /usr/src/app/${CONNECTOR_DIR}/dist/index.js "\$@"
EOF
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]