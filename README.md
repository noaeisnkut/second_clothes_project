# Kubernetes Application Deployment with Terragrunt, ArgoCD, and GitHub Actions

This repository contains both application code and deployment tools used to manage applications running on Kubernetes clusters. It integrates infrastructure provisioning, GitOps synchronization, and CI/CD automation using a unified workflow. The repository includes:

- Application source code
- Helm charts for Kubernetes deployments
- ArgoCD manifests for GitOps
- GitHub Actions workflows for CI/CD
- Terragrunt/Terraform configuration for provisioning AWS infrastructure

---

##  Deployment Flow

### 1. Provision Infrastructure and Deploy Applications

Run the following command from the Terragrunt root directory:

```bash
terragrunt run-all apply
This will create all infrastructure components and deploy all applications across environments.

**IAM Roles & Add-ons**:

The deployment automatically includes IAM roles and policies required for:
1. Cluster Autoscaler
2. AWS Load Balancer Controller

These roles are linked to Kubernetes ServiceAccounts using IRSA (IAM Roles for Service Accounts), ensuring secure and granular IAM permissions.
All relevant Helm charts—including the AWS Load Balancer Controller—are installed automatically as part of the provisioning process.

Post-Deployment Verification!

**get in the argo ui**:
show the password:
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 --decode
echo

type : username = admin (default username in every run)

display portfowording to open the argo ui in loacl browser:
kubectl port-forward svc/argocd-server -n argocd 8080:443

his forwards:
Local port: 8080
ArgoCD server port: 443
Namespace: argocd

After deployment, you can verify cluster health and workloads using the following commands:
**Kubernetes commands**:
kubectl get nodes
kubectl get pods -A
kubectl get svc -A

**verify load balancer address config : **
kubectl get ingress flask-ingress -n staging -w - to shoe the alb address of app staging.

**now about the ci-cd : how does it work?**:
GitHub Actions → Docker Hub → Git repo update → ArgoCD auto-sync → Kubernetes cluster

**more info about the proccess:**

1.Developer Pushes Code to main with [dev] Tag
The developer commits and pushes code.
The commit message must contain [dev] so the CI/CD job will run.
This is the manual trigger for the DEV pipeline.


2. GitHub Actions Starts the Pipeline

GitHub sees the push event.
The job filters using:
if: contains(github.event.head_commit.message, '[dev]')
Only commits meant for DEV run this workflow.


3. Backend Tests Execute

GitHub Actions installs Python dependencies.
Runs pytest inside the backend folder.
Ensures code quality before deployment.



4. Sync Repository With Remote main

Workflow pulls the latest main from GitHub.
Ensures the runner is always synced with the actual repo before building.



5. Docker Image Build

GitHub Actions builds a new Docker image for your Flask backend.
Image tagged with the first 8 characters of the commit SHA.

6. Push Image to Docker Hub

The new image (with the SHA tag) is pushed to your Docker Hub repo.
Now ArgoCD/EKS will be able to pull this image when deploying.



7. Update Helm Chart Values

Inside values-dev.yaml, this line is updated:
flask.image: "noa10203040/flask_app:<sha>"
This ensures K8s will deploy the new image version.



8. Commit Helm Changes Back to GitHub

GitHub Actions commits the updated Helm values file.
Pushes the change to the main branch.
This change is what ArgoCD monitors.



9. ArgoCD Detects the Git Change (GitOps Pull Model)

ArgoCD continuously watches the Git repository.
It sees the Helm values file was updated.
It detects the new container image hash.


10. ArgoCD Syncs the DEV Application

ArgoCD automatically (or manually via sync button):
Updates the Deployment
Pulls the new Docker image from Docker Hub
Restarts pods
Rolls out the new version with zero downtime (RollingUpdate)

**Final Result: New Version Live in DEV EKS Cluster**

Your backend Flask app is now updated inside the EKS DEV environment!!

The diagram above visualizes the full CI/CD flow for the DEV environment.  
It shows how a Git commit tagged with `[dev]` triggers a GitHub Actions workflow that builds a Docker image, updates Helm values, commits the changes back to Git, and allows ArgoCD to automatically sync and deploy the new version to the EKS cluster.  
This image represents the GitOps model where Git is the single source of truth and ArgoCD continuously reconciles Kubernetes with the desired state stored in the repository:

<img width="287" height="687" alt="image" src="https://github.com/user-attachments/assets/675a1cd0-65ca-49c2-8f78-5852b04d0608" />



