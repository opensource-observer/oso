FROM ghcr.io/strrl/cloudflare-tunnel-ingress-controller:latest as binary

FROM alpine:3.19
COPY --from=binary /usr/bin/cloudflare-tunnel-ingress-controller /usr/bin/cloudflare-tunnel-ingress-controller
COPY ./cf-tunnel-wrapper.sh /usr/bin/cf-tunnel-wrapper.sh

