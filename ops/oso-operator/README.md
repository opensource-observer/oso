# OSO Kubernetes Operator

Kubernetes is great and terrible but it is, in general, the tool we have to live
with for containerized deployments. Alternatives, don't have nearly the same
kind of community managing it. One of those beautiful sets of tools is flux or
argocd for gitops. As we at OSO are fully managing our infrastructure with
gitops, there are often things that we need to manage outside of kubernetes that
are still part of infrastructure but we end up having to use a mish-mash of
manual tooling, terraform, and click-ops. This kubernetes operator is intended
as a collection of custom resource definitions that we need to ensure
