# 🚀 local-gpu-scheduler

**A dead-simple GPU scheduler for shared local machines.**  
Like Slurm's `srun`, but zero-install and ~200 lines of code.

> No cgroups. No database. No config files. Just `srun python train.py`.

---

## Install

```bash
curl -sSL https://raw.githubusercontent.com/GindaChen/local-gpu-scheduler/main/install.sh | bash
```

Or manually:

```bash
git clone https://github.com/GindaChen/local-gpu-scheduler.git
cd local-gpu-scheduler
echo 'export PATH="'$(pwd)':$PATH"' >> ~/.bashrc && source ~/.bashrc
```

**Requirements:** Python 3.8+, `nvidia-smi`, `curl`, `jq`

---

## Quick Start

```bash
# 1. Start server + TUI in tmux
srun-server start

# 2. Run a GPU job (blocks until GPU available)
srun python train.py --epochs 50

# 3. Multi-GPU
srun -n 4 torchrun --nproc_per_node=4 train.py
```

---

## Commands

### `srun` — run GPU jobs

```bash
srun [-n NUM_GPUS] command [args...]   # acquire GPUs + run
srun status                            # show scheduler status
srun jobs                              # list all jobs
srun update                            # self-update (git pull)
```

### `srun-server` — manage the server

```bash
srun-server start [--port PORT]        # start server + TUI in tmux
srun-server stop                       # stop the tmux session
srun-server status                     # check if running
srun-server fg [--port PORT]           # run server in foreground
srun-server tui                        # open TUI dashboard
```

### Monitor — TUI dashboard

```bash
srun-tui                               # live GPU bar + job table (q to quit)
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

## Server API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/status` | Server identity, uptime, GPU counts, queue depth |
| `GET` | `/jobs` | All jobs with id, status, gpus, pid |
| `POST` | `/acquire` | Request GPUs (blocks). Body: `{"pid": int, "num_gpus": int}` |

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `GPUSCHED_PORT` | `9123` | Server port |
| `GPUSCHED_URL` | `http://localhost:9123` | Where `srun` connects |

## Tests

```bash
python -m unittest test_scheduler -v
```
