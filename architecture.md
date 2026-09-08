
# AI Compute Fabric — Architecture

## 1. Overview

AI Compute Fabric is an **AI-aware compute control plane** for scheduling,
executing, observing, and managing AI workloads across accelerator-backed
infrastructure.

The project separates workload intent from infrastructure execution.

A client submits an AI workload describing requirements such as GPU type,
VRAM, priority, execution mode, container image, and runtime configuration.
The control plane then determines whether the workload can be admitted,
when it should be considered, which accelerator should receive it, how the
workload should be materialized, and how runtime state should be reconciled
back into control-plane state.

The architecture was developed incrementally from an in-memory GPU scheduler
into a system validated on **Amazon EKS with a real NVIDIA Tesla T4**.

The implemented system includes:

- workload admission
- priority queueing
- AI-aware GPU scheduling
- logical GPU allocation
- PostgreSQL state persistence
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

# 2. Architectural Principles

Several boundaries are intentionally preserved throughout the system.

## 2.1 Admission Is Not Scheduling

Admission answers:

> Should this workload be accepted by the platform?

Scheduling answers:

> Which currently available accelerator should execute it?

These responsibilities remain separate.

---

## 2.2 Queueing Is Not Placement

The priority queue determines:

> When should a workload be considered for scheduling?

The scheduler determines:

> Where should the workload run?

A queued workload does not imply that GPU capacity has already been allocated.

---

## 2.3 Scheduling Is Not Infrastructure Execution

The scheduler does not call Kubernetes.

Its responsibility is limited to producing a placement decision and reserving
logical accelerator capacity.

Infrastructure-specific execution is delegated to a runtime adapter.

This preserves the boundary:

```text
Scheduler
    ↓
SchedulingDecision
    ↓
WorkloadRunner
    ↓
Infrastructure Adapter
