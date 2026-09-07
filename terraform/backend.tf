terraform {
  backend "s3" {
    bucket       = "ai-compute-fabric-tfstate-882640845424-ap-south-1"
    key          = "ai-compute-fabric/dev/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
