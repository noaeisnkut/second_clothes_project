**This repository contains both application code and deployment/synchronization tools to manage applications on a Kubernetes cluster and sync them with a remote Git repository.**

The repository is stored on the `main` branch and consists of:

- Application development files (`backend/`, etc.)
- Helm chart files (`helm-chart/`)
- ArgoCD application manifests (`argocd/argocd-apps/`)


Deployment Instructions:

**Apply all infrastructure and applications using Terragrunt:**
run terragrunt run --all apply 
**Verify that all applications are synchronized and healthy in ArgoCD:**
kubectl get applications -n argocd
**Access your application via the ALB created by the ALB controller + Ingress:**
kubectl get ingress flask-ingress -n staging -w
