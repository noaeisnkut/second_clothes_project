
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = "${var.environment}-eks-cluster"
  kubernetes_version = "1.29"

  addons = {
    coredns                = {}
    eks-pod-identity-agent = { before_compute = true }
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
  }

  endpoint_public_access                = true
  enable_cluster_creator_admin_permissions = true
  enable_irsa = true 
  vpc_id                               = var.vpc_id
  subnet_ids                           = var.subnet_ids
  control_plane_subnet_ids             = var.control_plane_subnet_ids

  eks_managed_node_groups = {
    nodes1 = {
      ami_type       = "AL2023_x86_64_STANDARD"
      instance_types = var.eks_node_sizes
      min_size       = 1
      max_size       = 2
      desired_size   = 1
    }
  }

  tags = {
    Environment = var.environment
    Terraform   = "true"
  }
}

module "cluster_autoscaler_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-assumable-role-with-oidc"
  version = "~> 5.46.0"

  create_role                   = true
  role_name                     = "${var.environment}-cluster-autoscaler"
  provider_url                  = replace(module.eks.cluster_oidc_issuer_url, "https://", "")
  role_policy_arns              = [aws_iam_policy.cluster_autoscaler.arn]
  oidc_fully_qualified_subjects = ["system:serviceaccount:kube-system:cluster-autoscaler"]
}

resource "aws_iam_policy" "cluster_autoscaler" {
  name        = "${var.environment}-cluster-autoscaler-policy"
  description = "EKS Cluster Autoscaler permissions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeTags",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "ec2:DescribeLaunchTemplateVersions"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "kubernetes_service_account" "cluster_autoscaler_service_account" {
  metadata {
    name      = "cluster-autoscaler"
    namespace = "kube-system"
    annotations = {
      "eks.amazonaws.com/role-arn" = module.cluster_autoscaler_irsa.iam_role_arn
    }
  }
}

resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  namespace  = "kube-system"
  version    = "9.34.0" 

  values = [jsonencode({
    autoDiscovery = {
      clusterName = "${var.environment}-eks-cluster"
    }
    awsRegion = var.region
    rbac = {
      serviceAccount = {
        create = false
        name   = "cluster-autoscaler"
      }
    }
    extraArgs = {
      skip-nodes-with-system-pods    = false
      balance-similar-node-groups    = true
      skip-nodes-with-local-storage  = false
    }
  })]
  depends_on = [ module.cluster_autoscaler_irsa, resource.kubernetes_service_account.cluster_autoscaler_service_account ]
}



resource "aws_iam_policy" "flask_app_policy" {
  name        = "${var.environment}-flask-app-policy"
  description = "Permissions for Flask App to access Secrets Manager and S3 via IRSA"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"]
        Resource = "arn:aws:secretsmanager:${var.region}:${data.aws_caller_identity.current.account_id}:secret:flask-app-secret-*"
      },
      {
        Effect = "Allow"
        Action = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject", "s3:ListBucket", "s3:PutObjectAcl"]
        Resource = [
          "arn:aws:s3:::my-second-hand-clothes-storage",
          "arn:aws:s3:::my-second-hand-clothes-storage/*"
        ]
      }
    ]
  })
}
locals {
  environments = ["dev", "staging", "prod"]
}

resource "kubernetes_namespace" "all" {
  for_each = toset(local.environments)
  metadata {
    name = each.key
  }
}

resource "aws_iam_role" "flask_app_irsa_role" {
  name = "flask-app-irsa-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringLike = {
            "${replace(module.eks.cluster_oidc_issuer_url, "https://", "")}:sub" = "system:serviceaccount:*:flask-app-sa"
          }
        }
      }
    ]
  })

  depends_on = [
    module.eks
  ]
}
resource "aws_iam_role_policy_attachment" "flask_app_attach" {
  role       = aws_iam_role.flask_app_irsa_role.name
  policy_arn = aws_iam_policy.flask_app_policy.arn
}

resource "kubernetes_service_account" "flask_app_sa" {
  for_each = kubernetes_namespace.all

  metadata {
    name      = "flask-app-sa"
    namespace = each.value.metadata[0].name

    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.flask_app_irsa_role.arn
    }
  }
}
