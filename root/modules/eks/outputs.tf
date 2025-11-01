output "cluster_name" {
  description = "The name of the EKS cluster"

  value       = module.eks.cluster_id
}

output "cluster_endpoint" {
  description = "The endpoint for the EKS cluster"
  value       = module.eks.cluster_endpoint
}

output "oidc_issuer_url" {
  description = "The URL of the cluster's OIDC issuer"
  value    = data.aws_eks_cluster.this.identity[0].oidc[0].issuer
}
