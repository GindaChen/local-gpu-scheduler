# AGENTS.md — local-gpu-scheduler

> For AI agents and automation tools interacting with this project.

## What This Is

A minimal local GPU job scheduler. A Python server runs on port `9123` managing GPU allocation via `nvidia-smi`. The `srun` shell script is the primary user interface — it acquires GPUs then `exec`s the user's command.

## Architecture

```
srun (bash)  ──POST /acquire──▶  server.py (:9123)  ──▶  nvidia-smi
                                     │
                                     ├── /status   GET  identity + health
                                     ├── /jobs     GET  list all jobs
                                     └── /acquire  POST blocks until GPUs free
```

## Server Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server identity, uptime, GPU counts, queue depth |
| `GET` | `/jobs` | All jobs with id, status, gpus, pid |
| `POST` | `/acquire` | Request GPUs (blocks until assigned). Body: `{"pid": int, "num_gpus": int}` |

### Identifying the Server

To verify the server is running and is this scheduler:

```bash
curl -s localhost:9123/status | jq .
```

Expected response:
```json
{
  "service": "local-gpu-scheduler",
  "version": "0.1.0",
  "uptime_s": 3600,
  "port": 9123,
  "gpus_total": 8,
  "gpus_allocated": [0, 2],
  "jobs_running": 2,
  "jobs_queued": 1,
  "jobs_total": 5
}
```

Check `"service": "local-gpu-scheduler"` to confirm identity.

## Key Files

| File | Purpose |
|------|---------|
| `server.py` | HTTP server — FIFO queue, GPU dispatch, PID monitoring |
| `gpu.py` | Wraps `nvidia-smi` for GPU detection |
| `srun` | Shell CLI — acquires GPUs, sets `CUDA_VISIBLE_DEVICES`, `exec`s command |
| `run_server.py` | Entry point: `python run_server.py` |
| `test_scheduler.py` | Tests: `python -m unittest test_scheduler -v` |

## How to Use Programmatically

### Acquire GPUs (what `srun` does)

```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"pid": '$$$', "num_gpus": 1}' \
  http://localhost:9123/acquire
# Blocks until GPU assigned, returns: {"job_id": "abc123", "gpus": "0"}
```

### Check Server Health

```bash
curl -sf http://localhost:9123/status > /dev/null && echo "up" || echo "down"
```

### List Running Jobs

```bash
curl -s http://localhost:9123/jobs | jq '.[] | select(.status == "running")'
```

## Environment Variables

| Var | Default | Description |
|-----|---------|-------------|
| `GPUSCHED_PORT` | `9123` | Server port |
| `GPUSCHED_URL` | `http://localhost:9123` | Where `srun` connects |
