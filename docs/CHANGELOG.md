cd ~/ai-compute-fabric

cat > docs/CHANGELOG.md <<'EOF'
# Changelog

All notable changes to **AI Compute Fabric** are documented in this file.

The format follows the general principles of Keep a Changelog.

AI Compute Fabric evolved from a local GPU scheduling prototype into an
AI-aware compute control plane validated on Amazon EKS with real NVIDIA GPU
infrastructure, training and inference workloads, durable model artifacts,
managed inference, MCP-based operations, and observability.

---

## [Unreleased]

### Documentation

- Final architecture and portfolio documentation refinement.
- Production gaps and engineering trade-offs documentation.
- Architecture Decision Record cleanup and consolidation.

### Known Engineering Debt

- Queue processing can return a scheduling decision for an older pending job
  when multiple jobs are waiting in the in-memory queue.
- Head-of-line queue blocking remains possible.
- Kubernetes workload termination requires additional idempotency hardening.
- Dynamic GPU metric labels can retain stale series.
- API authentication and authorization are not implemented.
- Full multi-tenant workload isolation is not implemented.
- Production-grade autoscaling, high availability, and disaster recovery are
  outside the current portfolio scope.

---

## [0.5.0] - 2026-09-08

### Added — Durable Model Artifact Lifecycle

- Model artifact domain model.
- Artifact repository abstraction.
- PostgreSQL-backed artifact metadata persistence.
- `ArtifactService` lifecycle boundary.
- Alembic migration for the `model_artifacts` table.
- Job-to-artifact relationships.
- S3-backed artifact storage.
- Recursive artifact directory publication.
- Private Amazon S3 artifact bucket managed through Terraform.
- S3 versioning and server-side encryption.
- Public-access blocking for artifact storage.
- IAM Roles for Service Accounts (IRSA) for workload artifact access.
- Dedicated Kubernetes workload ServiceAccount.
- Artifact publication context injected into executed workloads.
- QLoRA artifact publisher using workload identity.
- Durable QLoRA adapter upload to Amazon S3.
- Artifact metadata registration through the API.

### Added — Artifact API

- `POST /artifacts`
- `GET /artifacts/{artifact_id}`
- `GET /jobs/{job_id}/artifacts`

### Validated

Real end-to-end QLoRA artifact lifecycle:

```text
Tesla T4
    ↓
CUDA
    ↓
Qwen2.5-0.5B-Instruct
    ↓
4-bit QLoRA Fine-Tuning
    ↓
Adapter Saved
    ↓
IRSA-Authenticated S3 Upload
    ↓
PostgreSQL Artifact Metadata
    ↓
ArtifactService
    ↓
Artifact REST API

