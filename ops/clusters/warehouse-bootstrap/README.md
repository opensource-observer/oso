The flux installation is now managed by the flux operator (so we can be
as consistent as possible across local and the production cluster).

If needing to reinstall flux manually, you will need to first install the flux
operator:

```bash
helm install flux-operator \
    oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator \
    --namespace flux-system --create-namespace
```

Now add the flux-system secret to allow the operator to pull the repository as
well as read/write to it for production automation:

```bash
kubectl create secret generic flux-system \
  --namespace=flux-system \
  --from-literal=username=${USERNAME} \
  --from-literal=password="${GITHUB_PAT_SECRET}"
```

In addition to the flux-system secret we also need to add a
`flux-system/webhook-token` for receiving events from github actions. To set
this up run:

```bash
kubectl create secret generic webhook-token \
  --namespace=flux-system \
  --from-literal=token="${GITHUB_WEBHOOK_SECRET}"
```

This secret is available in the shared secrets within OSO. It's used to notify
the system of new builds so the flux cluster quickly reacts to new images.

Finally, apply the bootstrap manifest:

```bash
kubectl apply -f ${environment}-flux-bootstrap.yaml
```
