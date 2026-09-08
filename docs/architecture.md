## 1. Overview

AI Compute Fabric is an **AI-aware compute control plane** for scheduling,
executing, observing, and managing GPU and AI workloads across self-hosted
and managed compute.

The system separates workload intent from infrastructure execution.

A client submits an AI workload describing requirements such as GPU type,
VRAM, priority, execution mode, container image, and runtime configuration.
The control plane determines:

- whether the workload should be admitted
- when it should be considered for scheduling
- which available accelerator should receive it
- how logical accelerator capacity should be reserved
- how the workload should be materialized
- how runtime state should be observed
- how runtime reality should be reconciled with persistent state
- how terminal workloads should release accelerator capacity

The project evolved from a local in-memory GPU scheduling prototype into a
control plane validated on **Amazon EKS with a real NVIDIA Tesla T4**.

The completed architecture includes:

- workload admission
- priority queueing
- AI-aware GPU scheduling
- logical GPU allocation
- PostgreSQL persistence
- Kubernetes workload execution
- dynamic NVIDIA GPU discovery
- runtime observation and reconciliation
- PyTorch GPU training
- QLoRA fine-tuning
- vLLM model serving
- durable model artifact publication
- Amazon Bedrock managed inference
- DevOps MCP operations
- Prometheus and Grafana observability

---

## 2. Architectural Principles

Several responsibilities are deliberately separated instead of being
collapsed into one scheduling component.

### Admission Is Not Scheduling

Admission answers:

> Should this workload enter the system?

It validates workload requirements before scheduling.

### Queueing Is Not Placement

Queueing answers:

> When should this accepted workload be considered?

Accepted jobs enter a priority-aware queue.

### Scheduling Is Not Infrastructure Execution

Scheduling answers:

> Which currently available accelerator should execute this workload?

The scheduler evaluates GPU candidates and produces a placement decision.

It does not create Kubernetes resources.

### Logical State Is Not Runtime State

A workload being logically scheduled does not prove that its Kubernetes
runtime is healthy or even running.

Runtime state is observed separately and reconciled back into the control
plane.

### GPU Telemetry Is Not GPU Reservation

The GPU Agent observes NVIDIA hardware and reports telemetry.

It does not reserve the accelerator it observes.

### Terminal Runtime State Releases Accelerator Capacity

When a batch workload completes or fails, reconciliation transitions the
control-plane job and releases its logical GPU allocation.

For service workloads, runtime termination occurs before logical GPU release.

The resulting responsibility model is:

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

## 3. High-Level Architecture

The primary self-hosted execution path is:

```text
Client
  ↓
FastAPI
  ↓
Job Orchestrator
  ↓
Admission Controller / Job Manager
  ↓                   ↓
Priority Queue      Job Repository
  ↓                   ↓
Queue Processor     PostgreSQL
  ↓
Scheduler
  ↓
Resource Manager / GPU Scorer / GPU Manager
  ↓
GPU Inventory
  ↓
SchedulingDecision
  ↓
WorkloadRunner
  ↓
Kubernetes Adapter
  ↓
Amazon EKS
  ↓
Batch Workload (Job)
        OR
Service Workload (Deployment + Service)
  ↓
Runtime Observer
  ↓
Reconciler
  ↓
Job State Update + GPU Release
```

Additional platform paths are:

```text
Training
  ↓
ArtifactStore
  ↓
Amazon S3

Artifact Metadata
  ↓
ArtifactService
  ↓
ArtifactRepository
  ↓
PostgreSQL
```

```text
Managed Inference API
  ↓
ManagedInferenceService
  ↓
ManagedInferenceProvider
  ↓
BedrockProvider
  ↓
AWS Bedrock Runtime
```

```text
Operational API
  ↓
MCPService
  ↓
Official MCP Client
  ↓
DevOps MCP Server
  ↓
Kubernetes Python API
  ↓
Amazon EKS
```

```text
Control Plane + GPU Telemetry
  ↓
Prometheus
  ↓
Grafana
```

---

## 4. Core Control Plane

The control plane coordinates workload lifecycle while keeping scheduling,
persistence, runtime execution, and infrastructure concerns separated.

Conceptually:

```text
FastAPI
   ↓
JobOrchestrator
   ├── AdmissionController
   ├── JobManager
   ├── Priority Queue
   ├── QueueProcessor
   ├── Scheduler
   └── WorkloadRunner
```

### FastAPI

FastAPI provides the external control-plane boundary.

The API exposes capabilities covering:

- job submission and inspection
- workload lifecycle operations
- GPU inventory
- GPU telemetry reporting
- runtime reconciliation
- managed inference
- MCP operations
- model artifact registration and retrieval
- health and readiness
- Prometheus metrics

The API delegates domain behavior rather than embedding scheduling or
infrastructure logic directly.

### Job Orchestrator

The Job Orchestrator coordinates the workload lifecycle.

Conceptually:

```text
Submit Job
    ↓
Validate / Admit
    ↓
Persist
    ↓
Enqueue
    ↓
Process Queue
    ↓
Schedule
    ↓
Persist Placement
    ↓
Materialize Runtime Workload
```

The orchestrator coordinates these operations while preserving the
responsibility boundaries of the underlying components.

---

## 5. Admission and Queueing

### Admission Controller

The Admission Controller determines whether a workload can enter the
scheduling system.

Current validation includes workload properties such as:

- requested GPU memory greater than zero
- supported GPU memory bounds
- non-negative priority

Invalid workloads are rejected before accelerator allocation.

### Priority Queue

Accepted jobs enter a priority-aware queue.

The queue controls when an accepted workload is considered by the scheduler.

The distinction is:

```text
Admission
    ↓
Should the workload enter?

Priority Queue
    ↓
When should it be considered?

Scheduler
    ↓
Where should it run?
```

This separation allows admission policy, queue behavior, and placement policy
to evolve independently.

---

## 6. Scheduling Architecture

The scheduler selects an accelerator satisfying workload resource
requirements.

The scheduling pipeline is:

```text
Pending Job
    ↓
Scheduler
    ↓
Candidate Filtering
    ├── GPU status
    ├── GPU type
    └── VRAM capacity
    ↓
GPU Scoring
    ↓
Best Candidate
    ↓
GPUManager.allocate_gpu()
    ↓
SchedulingDecision
```

A `SchedulingDecision` contains placement information such as:

- GPU identifier
- node identifier
- scheduling score

The scheduler performs **placement and logical reservation only**.

It does not call the Kubernetes API.

This is a core architectural invariant:

```text
Scheduler
    ↓
SchedulingDecision

NOT

Scheduler
    ↓
Kubernetes API
```

Infrastructure execution starts only after the scheduling decision has been
produced.

---

## 7. GPU Resource Model

A GPU is represented as a control-plane resource independently from
Kubernetes.

The model contains information such as:

```text
GPU
├── id
├── type
├── total VRAM
├── free VRAM
├── utilization
├── temperature
├── status
└── node_id
```

Logical GPU states include:

```text
AVAILABLE
ALLOCATED
UNHEALTHY
DRAINING
```

### GPU Manager

The GPU Manager owns logical accelerator allocation and release.

Typical allocation lifecycle:

```text
AVAILABLE
    ↓ allocate
ALLOCATED
    ↓ terminal workload
AVAILABLE
```

The scheduler requests allocation through the GPU Manager rather than directly
mutating GPU inventory.

This centralizes logical accelerator ownership.

---

## 8. Dynamic GPU Discovery

Local development and automated tests can use simulated GPU inventory.

The real EKS environment uses dynamically discovered NVIDIA hardware.

The discovery path is:

```text
NVIDIA GPU
    ↓
nvidia-smi
    ↓
GPU Collector
    ↓
GPU Agent
    ↓
POST /gpu/reports
    ↓
Control-Plane GPU Inventory
```

Reported information includes:

- GPU UUID
- GPU model
- total VRAM
- free VRAM
- utilization
- temperature
- logical status
- Kubernetes node identity

This produces two deliberately separate inventory modes:

```text
Development / Tests
    → Simulated GPU Inventory

Real EKS
    → Dynamically Discovered NVIDIA Inventory
```

The GPU Agent observes hardware without requesting the GPU as a workload
resource.

Therefore telemetry collection does not consume or logically reserve the GPU
capacity required by scheduled AI workloads.

---

## 9. Persistence Architecture

Control-plane persistence is abstracted behind repository interfaces.

```text
Domain / Service
       ↓
Repository Interface
       ↓
┌──────────────────────┐
│                      │
▼                      ▼
In-Memory          PostgreSQL
Repository         Repository
                       ↓
                   PostgreSQL
```

The in-memory repository supports isolated development and testing.

The PostgreSQL implementation provides durable control-plane state.

Persisted information includes:

- job identity
- lifecycle status
- GPU placement
- node placement
- workload identity
- workload specification
- model artifact metadata

Database schema evolution is managed using Alembic.

The architecture therefore avoids coupling core domain behavior directly to
a specific persistence implementation.

---

## 10. Job Lifecycle

The control plane tracks workload lifecycle independently from Kubernetes
object phases.

The primary lifecycle is:

```text
PENDING
    ↓
SCHEDULED
    ↓
RUNNING
    ↓
COMPLETED
```

Terminal alternatives include:

```text
FAILED
CANCELLED
```

The control plane owns this domain lifecycle.

Kubernetes owns runtime resources.

Runtime observation and reconciliation connect the two without making
Kubernetes status objects part of the core job model.

---

## 11. Execution Architecture

Scheduling and execution are intentionally separate.

The scheduler stops at `SchedulingDecision`.

Infrastructure execution begins through `WorkloadRunner`.

```text
Scheduler
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Kubernetes Adapter
    ↓
Kubernetes API
```

The runner receives workload intent and placement information and materializes
the required infrastructure resources.

The current real execution adapter is Kubernetes.

The control-plane architecture itself is not intrinsically coupled to Amazon
EKS; EKS is the validated Kubernetes execution environment.

This boundary allows infrastructure-specific behavior to remain outside the
scheduler.

---

## 12. Workload Specification

Runtime intent is represented through workload specification rather than
hard-coded application behavior.

A workload specification can describe properties such as:

- container image
- command
- arguments
- environment
- execution mode
- ports
- runtime configuration

This allows the same control plane to execute different AI workload classes.

Validated workload types include:

- PyTorch training
- QLoRA fine-tuning
- vLLM inference

The workload specification is persisted so control-plane state retains the
runtime intent associated with a job.

---

## 13. Batch Execution

Finite workloads use batch execution semantics.

The Kubernetes adapter materializes batch workloads as Kubernetes Jobs.

```text
AI Workload
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Kubernetes Job
    ↓
Pod
    ↓
GPU Workload
```

PyTorch training and QLoRA fine-tuning use this execution mode.

After the runtime reaches a terminal state, reconciliation updates the
control-plane lifecycle and releases logical accelerator capacity.

---

## 14. Service Execution

Long-running inference workloads require different runtime semantics.

Service-mode workloads materialize:

```text
AI Service Workload
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Kubernetes Deployment
    +
Kubernetes Service
```

The Deployment owns the long-running model server.

The Service provides a stable network endpoint.

vLLM uses this execution path.

Batch and service workloads therefore share:

- admission
- queueing
- scheduling
- GPU allocation
- persistence
- runtime observation
- reconciliation

while using different infrastructure materialization strategies.

---

## 15. Runtime Observation

Creating a Kubernetes resource does not prove that an AI workload is
successfully running.

The runtime observation layer inspects infrastructure state.

```text
Kubernetes Job / Deployment
          ↓
Runtime Observer
          ↓
Normalized Runtime State
```

The observer translates Kubernetes-specific runtime information into a
normalized representation understood by the control plane.

This prevents Kubernetes status semantics from leaking throughout the core
domain.

---

## 16. Runtime Reconciliation

The reconciler compares runtime reality with persisted control-plane state.

For a running workload:

```text
Kubernetes Running
        ↓
Runtime Observer
        ↓
Reconciler
        ↓
Control Plane RUNNING
```

For successful batch completion:

```text
Kubernetes Completed
        ↓
Runtime Observer
        ↓
Reconciler
        ↓
Control Plane COMPLETED
        ↓
GPU Released
```

For runtime failure:

```text
Kubernetes Failed
        ↓
Runtime Observer
        ↓
Reconciler
        ↓
Control Plane FAILED
        ↓
GPU Released
```

For a service workload:

```text
Cancellation Request
        ↓
Terminate Deployment / Service
        ↓
Confirm Runtime Termination
        ↓
Update Control-Plane State
        ↓
Release GPU
```

This ordering prevents logical GPU capacity from being returned while a
runtime workload may still be consuming the accelerator.

---

## 17. Amazon EKS Infrastructure

Real infrastructure was provisioned using Terraform.

The validated environment included:

```text
AWS
└── VPC
    ├── Public Subnets
    ├── Private Subnets
    ├── Internet Gateway
    ├── NAT Gateway
    │
    └── Amazon EKS
        ├── CPU Managed Node Group
        │
        └── GPU Managed Node Group
             └── g4dn.xlarge
                  └── NVIDIA Tesla T4
```

Supporting infrastructure included:

- Amazon VPC
- public and private subnets
- Internet Gateway
- NAT Gateway
- Amazon EKS
- CPU managed node group
- GPU managed node group
- NVIDIA GPU support
- NVIDIA device plugin
- Amazon EBS CSI
- `gp3` persistent storage
- IAM roles and policies
- IAM Roles for Service Accounts
- private Amazon S3 artifact storage

The GPU node group supported scale-to-zero operation when accelerator capacity
was not required.

The real EKS environment used dynamic GPU discovery rather than simulated
inventory.

---

## 18. Real PyTorch Training

The first major real accelerator validation used CUDA-enabled PyTorch.

The complete path was:

```text
POST /jobs
    ↓
Admission
    ↓
Priority Queue
    ↓
Scheduler
    ↓
Real Tesla T4 Placement
    ↓
WorkloadRunner
    ↓
Kubernetes Job
    ↓
PyTorch + CUDA
    ↓
Training
    ↓
Runtime Completion
    ↓
Reconciliation
    ↓
Control Plane COMPLETED
    ↓
GPU AVAILABLE
```

Validation demonstrated:

- real NVIDIA Tesla T4 execution
- CUDA availability
- PyTorch GPU computation
- training on the scheduled GPU node
- Kubernetes workload completion
- runtime reconciliation
- logical accelerator release

This proved the scheduler-to-runtime lifecycle using real GPU infrastructure.

---

## 19. QLoRA Fine-Tuning

The platform was extended to execute parameter-efficient LLM fine-tuning using
QLoRA.

The final validated workload used:

```text
Base Model:
Qwen/Qwen2.5-0.5B-Instruct

Accelerator:
NVIDIA Tesla T4

Framework:
PyTorch + CUDA

Quantization:
4-bit

Trainable Parameters:
1,081,344

Total Parameters:
495,114,112

Trainable Percentage:
0.2184%
```

The observed training loss decreased from approximately:

```text
4.875121
    ↓
3.617788
```

The workload generated a QLoRA adapter at:

```text
/artifacts/qlora-adapter
```

This validated that AI Compute Fabric could coordinate a real LLM fine-tuning
workload through the same scheduling and execution architecture used by the
rest of the control plane.

---

## 20. Durable Model Artifact Architecture

Training output must survive the lifetime of an ephemeral training Pod.

The artifact subsystem therefore separates binary artifact storage from
artifact metadata.

```text
Training Workload
      │
      ├── Artifact Files
      │        ↓
      │   ArtifactStore
      │        ↓
      │    Amazon S3
      │
      └── Artifact Metadata
               ↓
        ArtifactService
               ↓
      ArtifactRepository
               ↓
          PostgreSQL
```

The artifact domain contains information such as:

```text
ModelArtifact
├── id
├── job_id
├── artifact_type
├── storage_uri
├── base_model
└── created_at
```

### Artifact Storage

`ArtifactStore` defines the storage abstraction.

The implemented durable backend is `S3ArtifactStore`.

Artifact directories are uploaded recursively while preserving their
contents.

Durable artifact locations follow:

```text
s3://<bucket>/<job_id>/<artifact_id>/
```

### Workload Identity with IRSA

Artifact-producing EKS workloads access AWS through IAM Roles for Service
Accounts.

```text
Kubernetes Pod
    ↓
ServiceAccount
    ↓
EKS OIDC
    ↓
IAM Role
    ↓
Amazon S3
```

Long-lived AWS credentials therefore do not need to be embedded inside the
training image.

### Artifact Publication

QLoRA artifact publication follows:

```text
QLoRA Training
    ↓
Save Adapter
    ↓
Upload Adapter to S3
    ↓
Register Artifact Metadata
    ↓
PostgreSQL
    ↓
Artifact API
```

Upload occurs before metadata registration.

This avoids intentionally creating a database pointer to an artifact that has
not reached durable object storage.

Artifact API operations include:

```text
POST /artifacts
GET  /artifacts/{artifact_id}
GET  /jobs/{job_id}/artifacts
```

The final QLoRA adapter was retained in private S3 after the expensive EKS/GPU
validation infrastructure was destroyed.

---

## 21. vLLM Inference Architecture

Self-hosted model serving uses the same scheduling and accelerator allocation
architecture as training.

The validated path was:

```text
Inference Job
    ↓
Admission
    ↓
Priority Queue
    ↓
GPU Scheduler
    ↓
Tesla T4 Placement
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Kubernetes Deployment
    +
Kubernetes Service
    ↓
vLLM
    ↓
Qwen2.5
    ↓
OpenAI-Compatible API
```

This demonstrated that the control plane supports both:

```text
Finite GPU Workloads
    → Kubernetes Job
    → Training / Fine-Tuning
```

and:

```text
Long-Running GPU Workloads
    → Deployment + Service
    → Model Serving
```

When the service workload is cancelled, runtime resources are terminated
before logical GPU capacity is released.

---

## 22. Managed Inference Architecture

Not every AI request should require platform-owned GPU capacity.

Managed inference therefore uses a separate provider abstraction.

```text
Client
    ↓
Managed Inference API
    ↓
ManagedInferenceService
    ↓
ManagedInferenceProvider
    ↓
BedrockProvider
    ↓
AWS Bedrock Runtime
    ↓
Foundation Model
```

The provider abstraction prevents API and service logic from becoming directly
coupled to AWS Bedrock SDK behavior.

Real managed inference was validated against Amazon Bedrock.

The project therefore demonstrates two complementary inference paths:

```text
Self-Hosted Inference

AI Compute Fabric
    ↓
GPU Scheduler
    ↓
Amazon EKS
    ↓
NVIDIA GPU
    ↓
vLLM
```

and:

```text
Managed Inference

AI Compute Fabric
    ↓
ManagedInferenceProvider
    ↓
AWS Bedrock
```

The control plane coordinates both approaches without pretending that their
execution semantics are identical.

---

## 23. DevOps MCP Architecture

AI Compute Fabric includes a Model Context Protocol operational integration.

The path is:

```text
AI Compute Fabric API
        ↓
MCPService
        ↓
Official MCP Client
        ↓
DevOps MCP Server
        ↓
Kubernetes Python API
        ↓
Amazon EKS
```

Implemented operational tools include:

```text
kubernetes_cluster_health
kubernetes_workload_status
gpu_cluster_status
```

The MCP integration exposes structured operational information while
preserving the separation between AI-native operations and scheduling logic.

The integration was validated against the real EKS environment.

MCP therefore acts as an operational interface to the infrastructure rather
than becoming part of accelerator placement.

---

## 24. Observability Architecture

AI Compute Fabric exposes control-plane and GPU telemetry through Prometheus.

```text
AI Compute Fabric
       ↓
    /metrics
       ↓
   Prometheus
       ↓
    Grafana
```

Control-plane metrics include:

- job submissions
- admission rejections
- scheduling attempts
- scheduling results
- job lifecycle transitions
- scheduling latency

GPU metrics include:

- total VRAM
- free VRAM
- utilization
- temperature
- logical GPU status

The observability model distinguishes two important questions:

```text
Infrastructure:
What is happening to the accelerator?

Control Plane:
What decisions is the scheduler making?
```

Both are required to understand AI infrastructure behavior.

Grafana dashboards were used to visualize real control-plane and GPU
telemetry during validation.

---

## 25. End-to-End Self-Hosted Execution

The completed self-hosted execution architecture is:

```text
Client
  ↓
FastAPI
  ↓
Job Orchestrator
  ↓
Admission Controller
  ↓
Priority Queue
  ↓
Queue Processor
  ↓
AI-Aware GPU Scheduler
  ↓
GPU Scoring
  ↓
GPU Manager
  ↓
Dynamic GPU Inventory
  ↓
SchedulingDecision
  ↓
WorkloadRunner
  ↓
Kubernetes Adapter
  ↓
Amazon EKS
  ↓
NVIDIA Tesla T4
  ↓
PyTorch / QLoRA / vLLM
  ↓
Runtime Observer
  ↓
Reconciler
  ↓
PostgreSQL State
  ↓
GPU Release
```

For artifact-producing training workloads:

```text
QLoRA Training
  ↓
Adapter
  ↓
IRSA
  ↓
Amazon S3
  ↓
ArtifactService
  ↓
ArtifactRepository
  ↓
PostgreSQL
  ↓
Artifact API
```

The broader platform also exposes:

```text
Managed AI
    → AWS Bedrock

AI-Native Operations
    → MCP → Kubernetes API

Observability
    → Prometheus → Grafana
```

---

## 26. Major Architectural Invariants

### Invariant 1 — Scheduler Does Not Control Kubernetes

The scheduler produces placement decisions.

Infrastructure adapters materialize workloads.

```text
Scheduler
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Infrastructure Adapter
```

### Invariant 2 — Admission, Queueing, and Scheduling Are Separate

```text
Admission = Should the workload enter?
Queue     = When should it be considered?
Scheduler = Where should it run?
```

### Invariant 3 — GPU Manager Owns Logical Allocation

Accelerator allocation and release occur through the GPU Manager.

### Invariant 4 — Runtime Reality Must Be Observed

A logically scheduled workload is not automatically assumed to be running.

Infrastructure state is explicitly observed.

### Invariant 5 — Runtime State Must Be Reconciled

Infrastructure reality is translated back into persistent control-plane
state.

### Invariant 6 — Terminal Workloads Release GPU Capacity

Completed, failed, and cancelled workloads must not leave logical accelerator
reservations indefinitely.

### Invariant 7 — Service Termination Precedes GPU Release

Long-running runtime resources are terminated before logical accelerator
capacity is returned.

### Invariant 8 — Real EKS Uses Real GPU Discovery

Simulation is available for development and testing.

Real EKS scheduling uses dynamically reported NVIDIA hardware.

### Invariant 9 — GPU Telemetry Does Not Reserve GPUs

The GPU Agent observes accelerators without consuming the workload GPU
resource.

### Invariant 10 — Durable Artifacts Live Outside Workload Containers

Model artifacts intended for later use are persisted to object storage.

PostgreSQL stores artifact metadata and durable storage references.

### Invariant 11 — Workloads Use Cloud Identity

AWS access from EKS workloads uses Kubernetes ServiceAccount-based identity
and IRSA rather than embedded long-lived AWS credentials.

### Invariant 12 — Managed and Self-Hosted Inference Remain Separate

vLLM uses platform-controlled GPU infrastructure.

Bedrock uses provider-managed inference infrastructure.

Both are exposed through the broader control plane without collapsing their
different execution semantics.

---

## 27. Failure and Recovery Semantics

### Unschedulable Workload

If no eligible GPU exists, the workload remains pending rather than being
incorrectly marked as running.

### Runtime Failure

A failed runtime is reconciled as:

```text
Runtime FAILED
      ↓
Runtime Observer
      ↓
Reconciler
      ↓
Control Plane FAILED
      ↓
GPU Released
```

### Runtime Completion

Successful batch completion follows:

```text
Kubernetes Complete
        ↓
Runtime Observer
        ↓
Reconciler
        ↓
Control Plane COMPLETED
        ↓
GPU AVAILABLE
```

### Service Termination

Service cancellation follows:

```text
Cancellation
    ↓
Terminate Runtime
    ↓
Confirm Termination
    ↓
Persist Terminal State
    ↓
Release GPU
```

### Persistent Control-Plane State

Durable job state is stored in PostgreSQL rather than depending on the
lifetime of the FastAPI process.

PostgreSQL persistence on EKS was validated with EBS-backed persistent
storage.

### Artifact Publication Failure

Artifact data is uploaded before metadata registration.

This ordering avoids intentionally registering metadata for an artifact that
was never uploaded.

A failure after successful object upload but before metadata registration can
leave an orphaned S3 object prefix. Automated orphan cleanup is outside the
current project scope.

### Known Queue Consistency Debt

The current in-memory queue implementation has a known edge case when an older
pending workload remains at the queue head while a newer workload is submitted
through the synchronous submission path.

This can create a mismatch between the job associated with the HTTP request
and the scheduling decision returned for the queue head.

The issue is documented as engineering debt rather than hidden or patched with
an architecture-breaking workaround.

---

## 28. Testing Architecture

The project uses automated tests across the major architectural boundaries.

Coverage includes:

- admission behavior
- queue behavior
- scheduling
- GPU filtering and scoring
- GPU allocation and release
- GPU telemetry
- job orchestration
- job repositories
- PostgreSQL persistence
- workload specifications
- Kubernetes execution
- runtime observation
- reconciliation
- managed inference
- MCP integration boundaries
- artifact persistence
- S3 artifact storage
- QLoRA artifact publication
- API behavior

The final implementation checkpoint reached:

```text
156 passed
```

Automated testing was complemented by real infrastructure validation.

The overall validation model is:

```text
Unit / Integration Tests
          +
Real AWS Infrastructure
          +
Real Amazon EKS
          +
Real NVIDIA Tesla T4
          +
Real AI Workloads
```

Real workload validation included:

- scheduler placement onto a real T4
- CUDA-enabled PyTorch training
- QLoRA fine-tuning
- vLLM model serving
- durable S3 artifact publication
- Amazon Bedrock managed inference
- MCP operations against EKS
- Prometheus/Grafana telemetry

---

## 29. Production Boundaries and Known Trade-offs

AI Compute Fabric is an AI infrastructure engineering and portfolio project,
not a production multi-tenant GPU cloud.

The current implementation deliberately demonstrates architectural depth
without claiming production controls that were not implemented.

Production capabilities outside the current scope include:

- API authentication and authorization
- strong multi-tenant isolation
- production secrets management
- Kubernetes NetworkPolicies
- comprehensive audit logging
- hardened workload sandboxing
- multi-AZ database architecture
- highly available control-plane services
- automated disaster recovery
- distributed durable queueing
- advanced scheduling fairness
- preemption
- production quota enforcement
- production GPU autoscaling integration
- hardened TLS ingress
- comprehensive image signing and supply-chain controls
- automated credential rotation
- complete artifact provenance

Infrastructure trade-offs used during validation included:

- a single NAT Gateway rather than multi-AZ NAT architecture
- a development-oriented public EKS API endpoint
- temporary broad administrative access during infrastructure validation
- non-persistent Prometheus storage
- development-oriented EBS configuration
- GPU capacity created for validation and later destroyed to control cost

Known implementation debt includes:

- head-of-line queue blocking
- queue decision consistency when older pending jobs exist
- additional termination idempotency hardening
- stale GPU metric label cleanup
- deployment-time database migration automation
- additional provider error normalization

These limitations are documented deliberately.

They define the boundary between the validated engineering system and the
additional controls required for a production-scale AI compute service.

---

## 30. Architecture Summary

AI Compute Fabric demonstrates the following control-plane journey:

```text
AI Workload Intent
      ↓
Admission
      ↓
Priority Queue
      ↓
AI-Aware GPU Scheduling
      ↓
Logical Accelerator Allocation
      ↓
SchedulingDecision
      ↓
Infrastructure Execution
      ↓
Real NVIDIA GPU
      ↓
Training / Fine-Tuning / Serving
      ↓
Runtime Observation
      ↓
Reconciliation
      ↓
Persistent State
      ↓
GPU Release
```

For durable training output:

```text
Training
    ↓
Model Artifact
    ↓
IRSA
    ↓
Amazon S3
    ↓
Artifact Metadata
    ↓
PostgreSQL
    ↓
Artifact API
```

Alongside self-hosted accelerator execution, the architecture supports:

```text
Managed Inference
    → AWS Bedrock

AI-Native Operations
    → Model Context Protocol

Model Artifacts
    → Amazon S3 + PostgreSQL

Observability
    → Prometheus + Grafana
```

The central architectural principle is:

> **AI Compute Fabric coordinates AI compute; it does not replace the
> infrastructure that executes it.**

Kubernetes, Amazon EKS, NVIDIA GPUs, PyTorch, vLLM, and AWS Bedrock remain
execution technologies.

AI Compute Fabric provides the control plane that reasons about workload
admission, priority, placement, accelerator allocation, infrastructure
execution, runtime state, reconciliation, durable artifacts, and operational
visibility across those technologies.


