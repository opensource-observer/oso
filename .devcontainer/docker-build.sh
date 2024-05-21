#! /bin/bash

docker buildx build --platform linux/amd64 -t infuseai/oso-dev-container:3.11 .. -f Dockerfile