# Contributing to AI Compute Fabric

Thank you for your interest in contributing to AI Compute Fabric.

AI Compute Fabric is an **AI-aware compute control plane** for scheduling,
executing, observing, and managing GPU and AI workloads.

Contributions should preserve the architectural boundaries described in
[`architecture.md`](architecture.md).

---

## 1. Development Principles

Changes should favor:

- clear architectural boundaries
- small, focused components
- explicit domain responsibilities
- strong typing
- automated tests
- explicit error handling
- backward compatibility where practical
- infrastructure-independent control-plane logic
- documentation for architectural changes

Avoid coupling components simply to reduce code.

In particular, preserve the distinction between:

```text
Admission      = Should the workload enter?
Queue          = When should it be considered?
Scheduler      = Where should it run?
GPU Manager    = Who owns logical GPU allocation?
WorkloadRunner = How should it be materialized?
Observer       = What is actually happening?
Reconciler     = Does control-plane state match runtime reality?
```

---

## 2. Important Architectural Boundaries

### Scheduler

The scheduler is responsible for accelerator placement.

It may:

- evaluate GPU candidates
- filter GPUs by workload requirements
- score eligible GPUs
- select a placement
- request logical GPU allocation
- produce a `SchedulingDecision`

It should **not directly create Kubernetes resources**.

Infrastructure execution belongs behind `WorkloadRunner`.

### GPU Manager

The GPU Manager owns logical accelerator allocation and release.

Do not introduce independent GPU-allocation state in unrelated components.

### Workload Execution

Infrastructure-specific execution belongs behind execution abstractions.

The current real implementation uses Kubernetes, but core scheduling logic
should not depend directly on Kubernetes APIs.

### Runtime State

Do not assume that successful scheduling means a workload is running.

Runtime state must be observed and reconciled back into control-plane state.

### Persistence

Domain and service logic should use repository abstractions rather than
depending directly on PostgreSQL implementation details.

### Artifacts

Artifact binary data and artifact metadata remain separate:

```text
Artifact Files
    → ArtifactStore
    → Amazon S3

Artifact Metadata
    → ArtifactRepository
    → PostgreSQL
```

### Managed Inference

Provider-specific behavior should remain behind the managed inference provider
abstraction.

### MCP

MCP provides an AI-native operational interface.

MCP tooling should not become part of accelerator placement or GPU allocation
logic.

---

## 3. Repository Structure

The primary project areas are:

```text
src/compute_fabric/
├── api/                 # FastAPI control-plane API
├── artifacts/           # model artifact lifecycle and storage
├── common/              # shared domain definitions
├── execution/           # workload execution, observation and reconciliation
├── gpu/                 # GPU inventory, manager, discovery and reporting
├── jobs/                # job lifecycle and orchestration
├── managed_inference/   # managed inference provider abstraction
├── mcp/                 # DevOps MCP integration
├── queue/               # admission and priority queueing
├── scheduler/           # placement and GPU scoring
├── storage/             # job repository implementations
└── telemetry/           # Prometheus metrics

examples/
├── training/            # PyTorch GPU training
├── qlora/               # QLoRA fine-tuning and artifact publication
└── vllm/                # vLLM model serving

kubernetes/              # Kubernetes manifests and EKS overlay
terraform/               # AWS / EKS infrastructure
observability/           # Prometheus and Grafana
migrations/              # Alembic database migrations
tests/                   # automated test suite
docs/                    # project documentation and evidence
```

---

## 4. Development Setup

Create and activate a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install project dependencies using the repository's dependency configuration.

For example:

```bash
pip install -r requirements.txt
```

Development environments may require additional infrastructure or credentials
for integration paths involving:

- PostgreSQL
- Kubernetes
- Amazon EKS
- Amazon S3
- Amazon Bedrock

Unit tests should not require real GPU infrastructure unless the test is
explicitly intended as infrastructure validation.

---

## 5. Running Tests

Run the complete automated test suite before submitting changes:

```bash
pytest -v
```

The final documented implementation checkpoint reached:

```text
156 passed
```

A contribution should not knowingly introduce regressions into previously
passing tests.

For focused development, individual test modules may be executed first, but
the complete suite should be run before considering the change complete.

---

## 6. Database Changes

Persistent schema changes must use Alembic migrations.

Migration files belong under:

```text
migrations/versions/
```

When introducing persistent fields or entities:

1. update the relevant domain/repository behavior
2. create the corresponding migration
3. test repository behavior
4. validate upgrade behavior
5. update documentation when the persisted architecture changes

Do not rely on manual database changes as the permanent project definition.

---

## 7. Kubernetes Changes

Kubernetes resources are organized under:

```text
kubernetes/base/
kubernetes/overlays/eks/
```

Keep reusable resources in the base where appropriate and AWS/EKS-specific
configuration in the EKS overlay.

Changes involving workload execution should preserve the boundary:

```text
Scheduler
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Kubernetes Adapter
```

Do not move Kubernetes API calls into the scheduler.

---

## 8. Infrastructure Changes

AWS infrastructure is maintained under:

```text
terraform/
```

Infrastructure changes should be:

- reviewable
- reproducible
- narrowly scoped
- validated before application
- documented when they affect architecture or security

Do not commit cloud credentials, private keys, tokens, or other secrets.

Development infrastructure should be destroyed when it is no longer required
if retaining it would create unnecessary cloud cost.

---

## 9. Security

Review [`SECURITY.md`](SECURITY.md) before making changes that affect:

- IAM
- IRSA
- Kubernetes RBAC
- model artifacts
- Amazon S3
- API exposure
- networking
- managed inference
- MCP
- secrets
- workload execution

Do not claim production security properties that have not been implemented and
validated.

---

## 10. Documentation

Architectural changes should update:

```text
docs/architecture.md
```

Security-impacting changes should update:

```text
docs/SECURITY.md
```

Significant engineering milestones should update:

```text
docs/CHANGELOG.md
```

Evidence images belong under:

```text
docs/screenshots/
```

Avoid adding duplicate documentation files when an existing canonical document
can be updated instead.

---

## 11. Pull Request Expectations

A contribution should clearly explain:

- what changed
- why the change is required
- which architectural component is affected
- how the change was validated
- whether persistence or migrations changed
- whether Kubernetes or Terraform changed
- whether security implications exist
- whether documentation requires updating

Prefer small, reviewable changes over unrelated modifications bundled into a
single pull request.

---

## 12. Known Engineering Debt

The repository intentionally documents known engineering debt rather than
hiding it.

Examples include:

- head-of-line queue blocking
- queue decision consistency with older pending jobs
- additional workload termination idempotency
- stale dynamic GPU metric series
- automated deployment-time database migrations
- additional managed inference error normalization

A contribution addressing one of these areas should preserve existing
architectural boundaries rather than bypassing them with a local workaround.

---

## 13. Scope

AI Compute Fabric is currently an AI infrastructure engineering and portfolio
project.

Contributions should strengthen the existing control-plane architecture rather
than turning the repository into a collection of unrelated AI, Kubernetes, or
cloud features.

The guiding principle remains:

> **AI Compute Fabric coordinates AI compute; it does not replace the
> infrastructure that executes it.**
