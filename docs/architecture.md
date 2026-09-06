# Architecture

## Overview

AI Compute Fabric is designed as an AI-aware GPU compute control plane.

The control plane receives workload requests, validates them, places them into a priority queue, evaluates available GPU resources, selects an appropriate GPU, and manages the lifecycle of the workload.

## High-Level Flow

```text
Client
  |
  v
FastAPI
  |
  v
Job Orchestrator
  |
  v
Admission Controller
  |
  v
Priority Queue
  |
  v
Queue Processor
  |
  v
Scheduler
  |
  +--> Resource Manager
  |
  +--> GPU Scorer
  |
  +--> GPU Manager
           |
           v
      GPU Inventory
