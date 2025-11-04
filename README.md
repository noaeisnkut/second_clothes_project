**This repository contains both application code and deployment/synchronization tools to manage applications on a Kubernetes cluster and sync them with a remote Git repository.**

The repository is stored on the `main` branch and consists of:

- Application development files (`backend/`, etc.)
- Helm chart files (`helm-chart/`)
- ArgoCD application manifests (`argocd/argocd-apps/`)
- github workflows


Deployment Instructions:

**Apply all infrastructure and applications using Terragrunt:**
run terragrunt run --all apply 
**Configure kubectl for the EKS cluster**:
aws eks update-kubeconfig --region us-east-1 --name prod-eks-cluster
aws eks update-kubeconfig --region us-east-1 --name dev-eks-cluster
**Verify that all applications are synchronized and healthy in ArgoCD:**
kubectl get applications -n argocd
**Access your application via the ALB created by the ALB controller + Ingress:**
kubectl get ingress flask-ingress -n staging -w
**when you want to push a commit and triiger dev or staging or prod env, just run:**
git add .(something that changed)
git commit -m "trigger workflow [dev]
git puah



