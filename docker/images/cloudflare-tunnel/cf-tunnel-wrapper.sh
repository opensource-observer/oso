# This is to enable the use of kube-secrets-init
#!/bin/sh
cloudflare-tunnel-ingress-controller \
--ingress-class=${INGRESS_CLASS} \
--controller-class=${CONTROLLER_CLASS} \
--cloudflare-api-token=${CLOUDFLARE_API_TOKEN} \
--cloudflare-account-id=${CLOUDFLARE_ACCOUNT_ID} \
--cloudflare-tunnel-name=${CLOUDFLARE_TUNNEL_NAME} \
--namespace=${NAMESPACE}
