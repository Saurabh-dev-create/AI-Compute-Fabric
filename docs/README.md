cat <<'EOF' > README.md
# AI Compute Fabric

AI-aware compute control plane for GPU workloads.

AI Compute Fabric is a Python-based control-plane project designed to manage GPU resources and intelligently schedule AI workloads across available compute resources.

## Current Capabilities

- GPU inventory management
- GPU health checking
- GPU VRAM-aware allocation
- GPU resource release
- GPU scoring
- GPU-aware scheduling
- Priority-based job queue
- Job admission control
- Job lifecycle management
- Job orchestration
- FastAPI REST API
- Automated unit tests

## Current Architecture

```text
                    +----------------------+
                    |      FastAPI API     |
                    +----------+-----------+
                               |
                               v
                    +----------------------+
                    |   Job Orchestrator   |
                    +----------+-----------+
                               |
              +----------------+----------------+
              |                                 |
              v                                 v
     +------------------+              +------------------+
     | Admission        |              | Job Manager      |
     | Controller       |              |                  |
     +--------+---------+              +------------------+
              |
              v
     +------------------+
     | Priority Queue   |
     +--------+---------+
              |
              v
     +------------------+
     | Queue Processor  |
     +--------+---------+
              |
              v
     +------------------+
     | Scheduler        |
     +--------+---------+
              |
       +------+------+
       |             |
       v             v
+-------------+ +-------------+
| GPU Scoring | | Resource    |
|             | | Manager     |
+------+------+ +------+------+
       |               |
       +-------+-------+
               |
               v
       +------------------+
       |    GPU Manager   |
       +--------+---------+
                |
                v
       +------------------+
       |   GPU Inventory  |
       +------------------+
