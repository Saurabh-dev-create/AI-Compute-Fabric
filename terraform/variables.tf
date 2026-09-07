variable "aws_region" {
  description = "AWS region for AI Compute Fabric infrastructure."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Project identifier used for AWS resource naming and tagging."
  type        = string
  default     = "ai-compute-fabric"
}

variable "environment" {
  description = "Infrastructure environment."
  type        = string
  default     = "dev"
}

variable "kubernetes_version" {
  description = "Amazon EKS Kubernetes control-plane version."
  type        = string
  default     = "1.36"
}
