FROM node:18 as build

RUN npm install -g pnpm

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN pnpm install && pnpm build:cloudquery