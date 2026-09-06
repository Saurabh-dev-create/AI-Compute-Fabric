cat <<'EOF' > CHANGELOG.md
# Changelog

All notable changes to AI Compute Fabric will be documented in this file.

The format follows the general principles of Keep a Changelog.

## [Unreleased]

### Added

- Project documentation structure.
- Architecture documentation.
- API documentation.
- Development guide.
- Deployment guide.
- Project roadmap.
- Architecture Decision Record structure.

### Planned

- Full API integration with `JobOrchestrator`.
- API-level automated tests.
- Job lifecycle API endpoints.
- Persistent job state.

## [0.1.0] - 2026-09-06

### Added

#### GPU Management

- GPU data model.
- GPU inventory.
- GPU registration and removal.
- GPU health checks.
- VRAM-aware GPU allocation.
- GPU resource release.

#### Scheduling

- GPU resource manager.
- GPU scoring.
- GPU-aware scheduler.
- scheduling decisions.
- prevention of allocation of already allocated GPUs.

#### Queue

- Priority job queue.
- Admission controller.
- Queue manager.
- Queue processor.

#### Jobs

- Job model.
- Job manager.
- Job state manager.
- Job orchestrator.
- Job lifecycle operations.

#### API

- FastAPI application.
- `GET /`
- `GET /gpus`
- `POST /jobs`
- `GET /jobs/{job_id}`

#### Testing

- Scheduler test suite.
- Job orchestrator test suite.
- 10 automated tests currently passing.

[Unreleased]: https://github.com/<owner>/<repository>/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/<owner>/<repository>/releases/tag/v0.1.0

