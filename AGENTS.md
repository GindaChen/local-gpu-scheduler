# AGENTS.md — local-gpu-scheduler

> For AI agents and automation tools interacting with this project.

## What This Is

A minimal local GPU job scheduler. A Python server on port `9123` manages GPU allocation via `nvidia-smi`. The `srun` shell script acquires GPUs then `exec`s the user's command.

**Repo:** https://github.com/GindaChen/local-gpu-scheduler

## Server Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server identity, uptime, GPU counts, queue depth |
| `GET` | `/jobs` | All jobs with id, status, gpus, pid |
| `POST` | `/acquire` | Request GPUs (blocks until assigned). Body: `{"pid": int, "num_gpus": int}` |

### Verify the server is running

```bash
curl -sf http://localhost:9123/status | jq .service
# Should return: "local-gpu-scheduler"
```

## Key Files

| File | Purpose |
|------|---------|
| `srun` | Shell CLI — acquires GPUs, `exec`s command |
| `server.py` | HTTP server — FIFO queue, PID monitoring |
| `gpu.py` | Wraps `nvidia-smi` for GPU detection |
| `tui.py` | Live dashboard |
| `run_server.py` | Entry point (`--detach`, `--port`) |

---

## Snippet for Other Projects

Drop this into any project's `AGENTS.md` to make agents use `srun`:

````markdown
## GPU Scheduling (Shared Machine)

This machine uses a shared GPU scheduler. Use `srun` to acquire GPUs before running GPU workloads.

```bash
# Run on 1 GPU
srun python train.py

# Run on multiple GPUs
srun -n 4 torchrun --nproc_per_node=4 train.py
```

If `srun` is not installed, install it:
```bash
git clone https://github.com/GindaChen/local-gpu-scheduler.git /tmp/gpu-scheduler
echo 'export PATH="/tmp/gpu-scheduler:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

If the scheduler server is not running (`srun` hangs or errors), start it:
```bash
python /tmp/gpu-scheduler/run_server.py --detach
```
````
