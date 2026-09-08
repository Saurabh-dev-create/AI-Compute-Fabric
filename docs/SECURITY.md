# Security Policy

## 1. Project Security Status

AI Compute Fabric is an **AI infrastructure engineering and portfolio project**
validated on real AWS, Amazon EKS, Kubernetes, and NVIDIA GPU infrastructure.

The project demonstrates practical cloud, workload identity, storage, and
infrastructure security controls, but it should **not be considered a
production-secure multi-tenant platform** in its current form.

The implementation prioritizes:

- AI compute control-plane architecture
- GPU scheduling
- workload execution
- runtime reconciliation
- durable model artifacts
- managed inference
- AI-native infrastructure operations
- observability

This document distinguishes between:

- security controls implemented and validated
- known security limitations
- controls required before production deployment

---

## 2. AWS IAM

AWS infrastructure uses IAM roles and policies rather than embedding
long-lived AWS credentials into application source code.

IAM is used for components including:

- Amazon EKS
- EKS managed node groups
- Amazon EBS CSI
- workload artifact access
- infrastructure provisioning

Infrastructure and workload permissions are separated where practical.

Terraform manages relevant IAM infrastructure so cloud permissions are
reviewable alongside the infrastructure configuration.

---

## 3. Workload Identity with IRSA

AI workloads requiring AWS access use **IAM Roles for Service Accounts
(IRSA)**.

The artifact publication path is:

```text
Kubernetes Workload
        ↓
Kubernetes ServiceAccount
        ↓
EKS OIDC Identity Provider
        ↓
IAM Role
        ↓
IAM Policy
        ↓
Amazon S3
```

This allows workloads to obtain temporary AWS credentials through workload
identity instead of embedding long-lived AWS access keys in container images,
Kubernetes manifests, or application configuration.

The durable artifact lifecycle uses this mechanism when QLoRA workloads publish
model adapters to Amazon S3.

---

## 4. Amazon S3 Artifact Security

Durable model artifacts are stored in a private Amazon S3 bucket.

Implemented controls include:

- S3 public-access blocking
- server-side encryption
- bucket versioning
- IAM-controlled access
- workload access through IRSA

The artifact architecture separates:

```text
Artifact Binary Data
    → Amazon S3

Artifact Metadata
    → PostgreSQL
```

The S3 bucket is not intended to provide public model distribution.

Artifacts are referenced through durable S3 URIs stored in artifact metadata.

---

## 5. Kubernetes Service Accounts

Artifact-producing workloads use a dedicated Kubernetes ServiceAccount.

The ServiceAccount acts as the Kubernetes identity associated with the
artifact workload IAM role.

Conceptually:

```text
Pod
 ↓
ServiceAccount
 ↓
IRSA
 ↓
AWS IAM Role
 ↓
S3 Permission
```

This is preferable to embedding AWS credentials directly into workload
environment variables or container images.

---

## 6. Infrastructure as Code

AWS and EKS infrastructure is represented using Terraform.

Infrastructure-as-code provides:

- reviewable infrastructure definitions
- reproducible cloud configuration
- explicit IAM configuration
- explicit network configuration
- managed node-group definitions
- storage configuration
- repeatable creation and destruction of validation infrastructure

The expensive EKS/GPU validation environment was destroyed after final
validation while the final trained QLoRA adapter was intentionally retained
in private Amazon S3.

Infrastructure-as-code improves reproducibility, but Terraform alone does not
guarantee that an environment is production hardened.

---

## 7. Kubernetes RBAC

Kubernetes RBAC is part of the infrastructure security boundary.

Cluster and workload identities should receive only the permissions required
for their responsibilities.

The project used Kubernetes permissions for components including:

- workload execution
- GPU discovery
- operational inspection
- storage integration

Some administrative access used during development and infrastructure
validation was intentionally broader than would be appropriate for a
production environment.

Production deployment would require a complete least-privilege RBAC review.

---

## 8. Persistence Security

PostgreSQL provides durable control-plane state.

Persisted data includes:

- job state
- scheduling placement
- workload identity
- workload specification
- model artifact metadata

The demonstrated environment validates persistence behavior, but does not
claim production database security.

Production hardening would require controls including:

- encrypted connections
- strong credential management
- credential rotation
- network isolation
- restricted database roles
- encrypted backups
- multi-AZ architecture
- backup validation
- disaster-recovery procedures
- database auditing where required

---

## 9. Container and Workload Security

AI workloads execute as containers on Kubernetes.

The project demonstrates workload materialization and GPU execution, but
complete production container hardening is outside the current scope.

Production requirements would include:

- minimal runtime images
- non-root execution where supported
- read-only root filesystems where practical
- dropped Linux capabilities
- seccomp profiles
- workload resource limits
- image vulnerability scanning
- signed container images
- trusted image provenance
- admission policy enforcement
- workload sandboxing for untrusted workloads

AI Compute Fabric should not currently be treated as a secure execution
environment for mutually untrusted tenant-supplied containers.

---

## 10. API Security

The current API demonstrates control-plane behavior and integration.

Production-grade authentication and authorization are not implemented as a
complete security boundary.

Before exposing the control plane to untrusted users, production deployment
would require:

- authenticated identities
- authorization policies
- role-based or policy-based access control
- tenant-aware resource authorization
- API rate limiting
- request size limits
- abuse protection
- audit logging
- secure session or token handling
- TLS termination

The current API should therefore be treated as an engineering interface rather
than an internet-facing production control plane.

---

## 11. Network Security

The AWS environment used VPC networking with public and private subnet
architecture.

The validation environment also used development-oriented networking choices
that should not be interpreted as final production configuration.

Known production gaps include:

- the EKS API endpoint was available publicly during validation
- Kubernetes NetworkPolicies were not implemented as a complete isolation
  boundary
- private-only control-plane access was not demonstrated
- production ingress and TLS architecture were not implemented

A production environment should use tighter network segmentation and restrict
control-plane and workload communication according to least privilege.

---

## 12. Secrets Management

The project avoids intentionally storing long-lived AWS credentials inside
workload images for artifact publication by using IRSA.

However, a complete production secrets-management architecture is outside the
current scope.

Production deployment should use an appropriate secrets system such as:

- AWS Secrets Manager
- AWS Systems Manager Parameter Store
- an external secrets controller
- another organization-approved secrets platform

Production controls should include:

- encryption at rest
- restricted access
- credential rotation
- auditability
- avoidance of secrets in source control
- avoidance of plaintext secrets in container images

---

## 13. Managed Inference Security

Managed inference is abstracted behind:

```text
ManagedInferenceService
        ↓
ManagedInferenceProvider
        ↓
BedrockProvider
        ↓
AWS Bedrock Runtime
```

AWS SDK credential resolution is used rather than hard-coding provider
credentials into the managed inference implementation.

Production deployment would additionally require:

- tightly scoped Bedrock IAM permissions
- model access governance
- request authorization
- usage quotas
- cost controls
- prompt and response logging policy
- sensitive-data handling policy
- provider audit controls

---

## 14. MCP Security

The DevOps MCP integration can expose operational Kubernetes information.

Implemented tools include:

```text
kubernetes_cluster_health
kubernetes_workload_status
gpu_cluster_status
```

Because operational tools can reveal infrastructure state, production MCP
deployment would require strong authorization boundaries.

Production controls should include:

- authenticated MCP clients
- tool-level authorization
- least-privilege Kubernetes credentials
- input validation
- audit logging
- restrictions on mutating operations
- tenant-aware resource filtering where applicable

The current MCP implementation demonstrates AI-native infrastructure
inspection rather than a production privileged-operations gateway.

---

## 15. Observability Security

Prometheus and Grafana expose infrastructure and control-plane telemetry.

Metrics can reveal operational information including:

- workload activity
- GPU inventory
- GPU utilization
- scheduling behavior
- job lifecycle information

Production observability should therefore be protected using:

- authentication
- authorization
- network restrictions
- TLS
- tenant-aware dashboard access where required
- controlled retention
- sensitive-label review

The demonstrated Prometheus environment did not use persistent storage and
should be treated as validation infrastructure.

---

## 16. Model Artifact Security

Model artifacts can contain valuable intellectual property and potentially
sensitive derived information.

The implemented artifact lifecycle provides private S3 storage and
IAM-controlled workload access.

Production artifact governance would additionally require:

- artifact provenance
- integrity verification
- retention policies
- lifecycle policies
- access auditing
- tenant-aware authorization
- optional customer-managed encryption keys
- malware or unsafe-artifact inspection where applicable
- controlled promotion between environments

Artifact metadata must not be treated as authorization merely because an
artifact record exists in PostgreSQL.

Authorization must be enforced independently.

---

## 17. Known Security Limitations

The current project does not claim implementation of:

- complete API authentication
- production authorization
- strong multi-tenant isolation
- comprehensive Kubernetes NetworkPolicies
- production secrets management
- complete audit logging
- hardened untrusted-workload sandboxing
- signed container-image enforcement
- complete software supply-chain controls
- automated credential rotation
- production database hardening
- encrypted EBS across every demonstrated storage path
- private-only EKS control-plane access
- comprehensive least-privilege IAM
- complete artifact provenance enforcement

Additional development-oriented infrastructure trade-offs included:

- public EKS API access during validation
- temporary broad administrative permissions
- non-persistent Prometheus storage
- development-oriented EBS configuration
- infrastructure optimized for portfolio validation rather than high
  availability

These limitations are intentionally documented rather than hidden.

---

## 18. Production Security Direction

A production security program for AI Compute Fabric should introduce controls
in layers.

### Identity

- user authentication
- service authentication
- workload identity
- short-lived credentials

### Authorization

- API authorization
- tenant isolation
- Kubernetes RBAC
- IAM least privilege
- artifact access control
- MCP tool authorization

### Network

- private control-plane access
- Kubernetes NetworkPolicies
- secure ingress
- TLS everywhere practical
- restricted database and observability access

### Workload Security

- non-root containers
- restrictive security contexts
- image scanning
- image signing
- admission policies
- workload sandboxing
- runtime threat detection where appropriate

### Data Security

- encrypted persistent storage
- protected backups
- controlled artifact access
- encryption-key governance
- data-retention policies

### Detection and Audit

- API audit events
- Kubernetes audit logging
- AWS CloudTrail
- security alerting
- artifact access logging
- privileged-operation auditing

---

## 19. Security Principles

The security direction of AI Compute Fabric follows several principles:

1. **Do not embed long-lived cloud credentials in workloads.**
2. **Separate workload identity from node identity where possible.**
3. **Keep model artifacts private by default.**
4. **Apply least privilege to cloud and Kubernetes permissions.**
5. **Treat AI workloads as potentially high-value compute and data assets.**
6. **Do not confuse infrastructure validation with production hardening.**
7. **Document security gaps explicitly rather than implying controls that do
   not exist.**
8. **Keep authorization separate from persistence and resource existence.**
9. **Treat operational AI interfaces such as MCP as privileged surfaces.**
10. **Design production multi-tenancy as a security boundary, not merely a
    metadata feature.**

---

## 20. Reporting a Security Issue

AI Compute Fabric is currently maintained as an engineering and portfolio
project.

Security issues should not be published with active credentials, secrets,
private keys, tokens, or sensitive infrastructure information.

When reporting a potential issue, include:

- affected component
- expected behavior
- observed behavior
- potential impact
- reproduction steps where safe
- suggested mitigation if known

Never include live cloud credentials or other secrets in an issue report.

---

## 21. Scope Statement

This security document describes the security posture of the demonstrated AI
Compute Fabric implementation.

It does not claim compliance certification, formal penetration testing, or
production multi-tenant security readiness.

The project demonstrates that security boundaries such as IAM, IRSA, private
artifact storage, workload identity, infrastructure-as-code, and Kubernetes
permissions were considered as part of the architecture.

Further hardening would be required before operating AI Compute Fabric as a
production service for untrusted users or organizations.
