# 🚀 local-gpu-scheduler

**A dead-simple GPU scheduler for shared local machines.**  
Like Slurm's `srun`, but zero-install and ~200 lines of code.

> No cgroups. No database. No config files. Just `srun python train.py`.

---

## Why?

On a shared GPU machine, people accidentally step on each other's GPUs. Slurm solves this but requires a database, daemon users, cgroup config, and 30+ minutes of setup.

This project gives you the same core workflow — **request GPUs → wait → run** — in a few files you can set up in 60 seconds.

---

## Install

```bash
git clone https://github.com/GindaChen/local-gpu-scheduler.git
cd local-gpu-scheduler

# Add srun to your PATH
echo 'export PATH="'$(pwd)':$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Requirements:** Python 3.8+, `nvidia-smi`, `curl`, `jq`

---

## Quick Start

**1. Start the server**

```bash
python run_server.py              # foreground
python run_server.py --detach     # background (daemon)
python run_server.py --port 8080  # custom port
```

**2. Run a GPU job**

```bash
srun python train.py --epochs 50                  # 1 GPU
srun -n 4 torchrun --nproc_per_node=4 train.py    # 4 GPUs
```

`srun` blocks until GPUs are available, sets `CUDA_VISIBLE_DEVICES`, then runs your command.

**3. Monitor**

```bash
python tui.py                              # live TUI dashboard (q to quit)
curl -s localhost:9123/status | jq .       # server health
curl -s localhost:9123/jobs   | jq .       # job list
```

---

## How It Works

```
┌─────────────────┐        ┌──────────────────────────┐
│  srun (bash)     │        │   server.py (:9123)       │
│                  │        │                           │
│ 1. POST /acquire ├───────▶│ 2. Queue request (FIFO)   │
│    {pid, ngpus}  │        │    Poll nvidia-smi for    │
│                  │        │    free GPUs               │
│ 3. Receive GPUs  │◀───────┤                           │
│                  │        │ 4. Monitor PID             │
│ 4. export CUDA_  │        │    When PID exits →        │
│    VISIBLE_DEVS  │        │    release GPUs            │
│                  │        │                           │
│ 5. exec command  │        └──────────────────────────┘
└─────────────────┘
```

---

## Server API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server identity, uptime, GPU counts, queue depth |
| `GET` | `/jobs` | All jobs with id, status, gpus, pid |
| `POST` | `/acquire` | Request GPUs (blocks). Body: `{"pid": int, "num_gpus": int}` |

---

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `GPUSCHED_PORT` | `9123` | Server port |
| `GPUSCHED_URL` | `http://localhost:9123` | Where `srun` connects |

---

## Files

| File | Description |
|------|-------------|
| `srun` | Shell CLI — acquires GPUs, sets env, `exec`s command |
| `server.py` | HTTP server — FIFO queue, GPU dispatch, PID monitor |
| `gpu.py` | Wraps `nvidia-smi` for GPU detection |
| `tui.py` | Curses dashboard — GPU bar, job table, server health |
| `run_server.py` | Entry point with `--detach` and `--port` flags |

---

## Slurm vs. local-gpu-scheduler

| | Slurm | This |
|---|---|---|
| Install time | 30+ min | 60 sec |
| Dependencies | munge, MySQL, slurmctld | Python 3, curl, jq |
| Config files | `slurm.conf` (100+ lines) | None |
| Root required | Usually | No |
| Multi-node | ✅ | ❌ Single machine |
| Fair-share / priorities | ✅ | ❌ FIFO only |
| Best for | Clusters, 10+ users | 1 machine, small team |

---

## Tests

```bash
python -m unittest test_scheduler -v
```
