# Kubernetes Application Deployment with Terragrunt, ArgoCD, and GitHub Actions

This repository contains both application code and deployment tools used to manage applications running on Kubernetes clusters.  
It integrates infrastructure provisioning, GitOps synchronization, and CI/CD automation using a unified workflow.  

## Repository Contents

- Application source code
- Helm charts for Kubernetes deployments
- ArgoCD manifests for GitOps
- GitHub Actions workflows for CI/CD
- Terragrunt/Terraform configuration for provisioning AWS infrastructure

---

## Deployment Flow

### 1. Provision Infrastructure and Deploy Applications

Run the following command from the Terragrunt root directory:

terragrunt run-all apply

This will create all infrastructure components and deploy all applications across environments.


**IAM Roles & Add-ons**
The deployment automatically includes IAM roles and policies required for:
Cluster Autoscaler
AWS Load Balancer Controller
These roles are linked to Kubernetes ServiceAccounts using IRSA (IAM Roles for Service Accounts), ensuring secure and granular IAM permissions.
All relevant Helm charts—including the AWS Load Balancer Controller—are installed automatically as part of the provisioning process.

**his command is meant to update your kubeconfig file (usually ~/.kube/config) so that you can connect to your EKS cluster using kubectl:**
aws eks update-kubeconfig --name dev-eks-cluster --region us-east-1 
**or in the other cluster:**
aws eks update-kubeconfig --name prod-eks-cluster --region us-east-1

Post-Deployment Verification
**Access ArgoCD UI**
# Show initial password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 --decode
echo

# Port-forward ArgoCD to localhost
kubectl port-forward svc/argocd-server -n argocd 8080:443

Username: admin
Local port: 8080 → ArgoCD server port 443
Namespace: argocd


**Verify Cluster Health and Workloads**:


kubectl get nodes
kubectl get pods -A
kubectl get svc -A

**Verify Load Balancer Address**:
kubectl get ingress flask-ingress -n staging -w

**CI/CD Process**
The CI/CD pipeline integrates GitHub Actions, Docker Hub, and ArgoCD. The flow is as follows:

**Step 1: Developer Pushes Code to Main with [dev] Tag
The developer commits and pushes code.**

The commit message must contain [dev] so the CI/CD job will run.
This is the manual trigger for the DEV pipeline.


**Step 2: GitHub Actions Starts the Pipeline**
GitHub sees the push event.
The job filters commits using:

if: contains(github.event.head_commit.message, '[dev]')
Only commits meant for DEV run this workflow.

**Step 3: Backend Tests Execute**
GitHub Actions installs Python dependencies.
Runs pytest inside the backend folder.
Ensures code quality before deployment.


**Step 4: Sync Repository With Remote Main**
Workflow pulls the latest main from GitHub.
Ensures the runner is always synced with the actual repository before building.


**Step 5: Docker Image Build**
GitHub Actions builds a new Docker image for the Flask backend.
Image tagged with the first 8 characters of the commit SHA.


**Step 6: Push Image to Docker Hub**
The new image (with SHA tag) is pushed to Docker Hub.
ArgoCD/EKS can now pull this image when deploying.


**Step 7: Update Helm Chart Values**
Inside values-dev.yaml, this line is updated:

flask.image: "noa10203040/flask_app:<sha>"
Ensures Kubernetes deploys the new image version.

**Step 8: Commit Helm Changes Back to GitHub**
GitHub Actions commits the updated Helm values file.
Pushes the change to the main branch.
This change is what ArgoCD monitors.


**Step 9: ArgoCD Detects the Git Change (GitOps Pull Model)**
ArgoCD continuously watches the Git repository.
It sees the Helm values file was updated.
Detects the new container image hash.


**Step 10: ArgoCD Syncs the DEV Application**
ArgoCD automatically (or manually via sync button):
Updates the Deployment
Pulls the new Docker image from Docker Hub
Restarts pods
Rolls out the new version with zero downtime (RollingUpdate)


**Final Result:**
The backend Flask app is now updated inside the EKS DEV environment.

## Visualization

The diagram above visualizes the full CI/CD flow for the DEV environment.  
It shows how a Git commit tagged with `[dev]` triggers a GitHub Actions workflow that builds a Docker image, updates Helm values, commits the changes back to Git, and allows ArgoCD to automatically sync and deploy the new version to the EKS cluster.  
This image represents the GitOps model where Git is the single source of truth and ArgoCD continuously reconciles Kubernetes with the desired state stored in the repository.
<img width="287" height="687" alt="image" src="https://github.com/user-attachments/assets/58524213-32cd-433f-b380-7d759a4ad8c5" />




