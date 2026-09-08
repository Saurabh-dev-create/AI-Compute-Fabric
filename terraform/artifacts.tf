resource "aws_s3_bucket" "artifacts" {
  bucket = "${var.project_name}-${var.environment}-artifacts-${data.aws_caller_identity.current.account_id}-${var.aws_region}"

  tags = {
    Name = "${var.project_name}-${var.environment}-artifacts"
  }
}

resource "aws_s3_bucket_public_access_block" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

data "aws_iam_policy_document" "artifact_workload_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Federated"
      identifiers = [
        aws_iam_openid_connect_provider.eks.arn,
      ]
    }

    actions = [
      "sts:AssumeRoleWithWebIdentity",
    ]

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(aws_eks_cluster.main.identity[0].oidc[0].issuer, "https://", "")}:sub"
      values   = ["system:serviceaccount:default:compute-fabric-workload"]
    }
  }
}

resource "aws_iam_role" "artifact_workload" {
  name = "${var.project_name}-${var.environment}-artifact-workload-role"

  assume_role_policy = data.aws_iam_policy_document.artifact_workload_assume_role.json

  tags = {
    Name = "${var.project_name}-${var.environment}-artifact-workload-role"
  }
}

data "aws_iam_policy_document" "artifact_workload" {
  statement {
    sid    = "ListArtifactBucket"
    effect = "Allow"

    actions = [
      "s3:ListBucket",
    ]

    resources = [
      aws_s3_bucket.artifacts.arn,
    ]
  }

  statement {
    sid    = "ArtifactObjects"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]

    resources = [
      "${aws_s3_bucket.artifacts.arn}/*",
    ]
  }
}

resource "aws_iam_role_policy" "artifact_workload" {
  name   = "${var.project_name}-${var.environment}-artifact-workload"
  role   = aws_iam_role.artifact_workload.id
  policy = data.aws_iam_policy_document.artifact_workload.json
}

output "artifact_bucket_name" {
  description = "S3 bucket used for durable model artifacts."
  value       = aws_s3_bucket.artifacts.bucket
}

output "artifact_workload_role_arn" {
  description = "IAM role assumed by model-producing workloads."
  value       = aws_iam_role.artifact_workload.arn
}
