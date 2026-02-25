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
# Clone
git clone https://github.com/GindaChen/local-gpu-scheduler.git
cd local-gpu-scheduler

# Add srun to your PATH
echo 'export PATH="'$(pwd)':$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Requirements:** Python 3.8+, `nvidia-smi`, `curl`, `jq`

---

## Setup

```bash
# Foreground (see logs in terminal)
python run_server.py

# Background (daemon mode)
python run_server.py --detach

# Custom port
python run_server.py --port 8080
```

---

## Usage

```bash
# Run on 1 GPU (blocks until available)
srun python train.py --epochs 50

# Run on 4 GPUs
srun -n 4 torchrun --nproc_per_node=4 train.py
```

### Monitor with the TUI dashboard

```bash
python tui.py
```

Shows a live view of GPU allocation, running/queued jobs, and PIDs. Press `q` to quit.

### Query server status

```bash
curl -s localhost:9123/status | jq .
curl -s localhost:9123/jobs   | jq .
```

---

## How It Works

```
srun (shell)          server.py (:9123)
─────────────         ─────────────────
1. Send PID ──POST──▶ /acquire
2. Block...           checks nvidia-smi
3. ◀── GPU IDs ───── returns free GPUs
4. export CUDA_       monitors PID
   VISIBLE_DEVICES
5. exec command       when PID exits →
                      release GPUs
```

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `GPUSCHED_PORT` | `9123` | Server port |
| `GPUSCHED_URL` | `http://localhost:9123` | Where `srun` connects |

## Tests

```bash
python -m unittest test_scheduler -v
```
