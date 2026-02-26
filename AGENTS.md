# AGENTS.md — local-gpu-scheduler

> For AI agents and automation tools interacting with this project.

**Repo:** https://github.com/GindaChen/local-gpu-scheduler

## Commands

| Command | Description |
|---------|-------------|
| `srun <cmd>` | Acquire 1 GPU and run command |
| `srun -n N <cmd>` | Acquire N GPUs and run command |
| `srun-agent <cmd>` | Like srun, but auto-retries with adjusted GPU count on failure |
| `srun-server start` | Start server + TUI in tmux (default) |
| `srun-server start --no-tmux` | Start server in foreground |
| `srun-server stop` | Stop the server |
| `srun-server status` | Check if server is running |
| `srun-server tui` | Open TUI dashboard |
| `srun status` | Query scheduler status |
| `srun jobs` | List running jobs |
| `srun update` | Self-update (git pull) |
| `srun-tui` | Standalone TUI dashboard |

## Server API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server identity, uptime, GPU counts, queue depth |
| `GET` | `/jobs` | All jobs with id, status, gpus, pid |
| `POST` | `/acquire` | Request GPUs (blocks). Body: `{"pid": int, "num_gpus": int}` |

### Verify the server

```bash
curl -sf http://localhost:9123/status | jq .service
# Returns: "local-gpu-scheduler"
```

## Key Files

| File | Purpose |
|------|---------|
| `srun` | Shell CLI — acquires GPUs, `exec`s command |
| `srun-agent` | Shell wrapper — auto-retries with GPU fix |
| `srun-server` | Shell CLI — start/stop/status server |
| `srun-tui` | Curses TUI dashboard |
| `server.py` | HTTP server — FIFO queue, PID monitoring |
| `gpu.py` | Wraps `nvidia-smi` for GPU detection |
| `run_server.py` | Server entry point |

---

## Snippet for Other Projects

Drop this into any project's `AGENTS.md` to make agents use `srun`:

````markdown
## GPU Scheduling (Shared Machine)

This machine uses a shared GPU scheduler. Use `srun` to acquire GPUs before running GPU workloads.

```bash
srun python train.py                           # 1 GPU
srun -n 4 torchrun --nproc_per_node=4 train.py # multi-GPU
srun-agent python train.py                     # auto-retry with GPU fix
```

If `srun` is not installed:
```bash
curl -sSL https://raw.githubusercontent.com/GindaChen/local-gpu-scheduler/main/install.sh | bash
```

If the scheduler server is not running:
```bash
srun-server start
```
````
