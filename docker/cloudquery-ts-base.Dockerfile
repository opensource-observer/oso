FROM node:18 as build

RUN npm install -g pnpm@^8.0.0

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN pnpm install && pnpm build:cloudquery