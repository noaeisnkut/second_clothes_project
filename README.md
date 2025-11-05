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

**code info**:
This is a Flask web application for managing second-hand clothes. It uses Flask-SQLAlchemy to connect to a PostgreSQL database and store user accounts (User) and product listings (AddClothe). Users can sign up, log in, add products with images, and delete their own products. Images are stored in S3, and URLs are generated with a presigned link for secure access.
The app retrieves sensitive information, like the database password, from AWS Secrets Manager using boto3, which is the AWS SDK for Python. Botocore is a lower-level library used internally by boto3 to handle requests, responses, and error handling with AWS services. Together, they allow the Flask app to securely interact with AWS services, such as S3 for image storage and Secrets Manager for fetching credentials, without hardcoding secrets in the code.
Environment variables are used for configuration, including AWS region, database connection details, and secret keys, making the app flexible for local development, Docker, or deployment in Kubernetes.

**why do i have db_dumps in my code?**:
**Migration to PostgreSQL**
I wanted all the pods in my cluster to be able to access a single, centralized database instead of relying on a local database on each node. So, I decided to move my data to PostgreSQL in the cloud using AWS RDS.
First, I created a PostgreSQL database in RDS, picked a recent version with Multi-AZ deployment, set up a username and password, enabled public access, and saved the database endpoint.
Next, I installed the psycopg2 driver in Flask and updated the connection string in my code to point to the RDS database instead of the local one.
Then, I exported only the data I needed from MySQL into an SQL dump and imported it into PostgreSQL using psql, loading it into the cloud database.
Now, all the pods in the cluster can access the database remotely, without depending on a local database.
Why PostgreSQL (RDS) instead of PVCs or node storage?
1. I/O limitations – Regular Kubernetes volumes don’t always handle high read/write throughput well, especially when many pods access them at the same time.
2. Availability across AZs – PVCs or PVs are usually tied to a single node or availability zone, so pods in other zones might not access them reliably. RDS with Multi-AZ solves this.
3. Scalability and durability – A managed cloud database takes care of failures, backups, replication, and maintenance automatically, which is much harder to handle manually with PVs/PVCs.
4. Best practice – When consistency, performance, and reliability matter, using a managed database service like RDS is much better than relying on local node storage.

**other alternative to postgress**:
1. Block storage volumes (EBS/PVCs) – I could have stored the database directly on a persistent volume backed by block storage. This would give a dedicated storage space for the database, but it’s tied to a single node or AZ, which makes it harder for pods in other zones to access it reliably. I/O performance could also become a bottleneck if many pods are reading/writing simultaneously.

2. S3 or object storage – I could have stored the database dump or snapshots in S3. This works for backups or static storage, but it’s not suitable as a live, transactional database, since S3 doesn’t support SQL queries or frequent read/write operations efficiently.
3. Exporting to MySQL or RDS Aurora – I could have replicated the data into a MySQL database or used Aurora. This can work, but the migration and schema adaptation would have been more complicated. Aurora is scalable and highly available like RDS Postgres, but since my app already depends on PostgreSQL-specific features, this would have added extra complexity.
4. PV + containerized PostgreSQL – I could have taken the SQL dump I created from MySQL via SQLAlchemy and loaded it into a PostgreSQL instance running inside a pod, using a temporary folder or persistent volume. This would allow me to test or migrate the database without immediately using RDS. However, I would still be responsible for managing backups, replication, failover, and availability across multiple AZs, which is much harder to handle manually compared to using a managed service like RDS.

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
**how to check if ci-cd works?!**:
in the remote, check for example the values-dev.yaml and look for  a change in the virsion of the image - if yes, congrats! 
you must also check if argo also synced the cluster, check it by :
kubectl get pods -n dev -o wide (to see the running pods)
and to describe each proccess in the pod:
 kubectl describe pod <pod> -n dev
you'll be lokking for the line:
Normal  Pulling    27m   kubelet            Pulling image "noa10203040/flask_app:90476060"
Normal  Pulled     27m   kubelet            Successfully pulled image "noa10203040/flask_app:90476060" in 19.539s (19.539s including waiting)
if both happen, you are good to go!




## Visualization

The diagram above visualizes the full CI/CD flow for the DEV environment.  
It shows how a Git commit tagged with `[dev]` triggers a GitHub Actions workflow that builds a Docker image, updates Helm values, commits the changes back to Git, and allows ArgoCD to automatically sync and deploy the new version to the EKS cluster.  
This image represents the GitOps model where Git is the single source of truth and ArgoCD continuously reconciles Kubernetes with the desired state stored in the repository.


<img width="287" height="687" alt="image" src="https://github.com/user-attachments/assets/58524213-32cd-433f-b380-7d759a4ad8c5" />







