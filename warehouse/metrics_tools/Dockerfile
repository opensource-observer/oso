FROM rancher/k3s:v1.30.6-k3s1 as k3s

FROM alpine:3

RUN apk update && apk add bash

COPY --from=k3s / /
VOLUME /var/lib/kubelet
VOLUME /var/lib/rancher/k3s
VOLUME /var/lib/cni
VOLUME /var/log

