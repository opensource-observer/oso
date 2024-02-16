FROM python:3.12-bookworm

RUN pip install poetry

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN poetry install
