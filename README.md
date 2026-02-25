# 🚀 local-gpu-scheduler

**A dead-simple GPU scheduler for shared local machines.**
Like Slurm's `srun`, but zero-install and ~130 lines of code.

> No cgroups. No database. No config files. Just `srun python train.py`.

---

## Why?

On a shared GPU machine, people accidentally step on each other's GPUs. Slurm solves this but requires a database, daemon users, cgroup config, and 30+ minutes of setup.

This project gives you the same core workflow — **request GPUs → wait → run** — in two files you can set up in 60 seconds.

---

## Install

```bash
# Clone
git clone https://github.com/GindaChen/local-gpu-scheduler.git
cd local-gpu-scheduler

# (Optional) Add srun to your PATH so everyone can use it
echo 'export PATH="'$(pwd)':$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Requirements:**
- Python 3.8+ (no pip packages needed)
- `nvidia-smi` on the machine
- `curl` and `jq` (usually pre-installed)

---

## Setup

**Start the server** (once, ideally in a `screen` or `systemd` service):

```bash
python run_server.py
# => gpusched server on :9123
```

That's it. The server runs on port `9123` by default.

<details>
<summary>💡 Run as a systemd service (recommended for production)</summary>

```bash
sudo tee /etc/systemd/system/gpusched.service <<EOF
[Unit]
Description=Local GPU Scheduler
After=network.target

[Service]
ExecStart=$(which python3) $(pwd)/run_server.py
WorkingDirectory=$(pwd)
Restart=always
User=$USER

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now gpusched
```
</details>

---

## Usage

### Run a job on 1 GPU

```bash
srun python train.py --epochs 50
```

`srun` blocks until a GPU is available, then runs your command with `CUDA_VISIBLE_DEVICES` set automatically.

### Run a multi-GPU job

```bash
srun -n 4 torchrun --nproc_per_node=4 train.py
```

### What happens under the hood

```
┌──────────────┐          ┌───────────────────┐
│  srun (bash) │──POST──▶ │  server.py (:9123) │
│  PID=12345   │  /acquire│                    │
│              │◀─blocks──│  checks nvidia-smi │
│              │          │  waits for free GPU│
│              │◀─200─────│  returns gpu=2     │
│              │          └───────┬────────────┘
│  export CUDA │                  │
│  _VISIBLE_   │                  │ monitors PID 12345
│  DEVICES=2   │                  │ every 1s
│              │                  │
│  exec python │                  │
│  train.py    │                  │
│  ...running..│                  │
│  (exits)     │                  │
│              │          ┌───────▼────────────┐
└──────────────┘          │  PID gone → GPU 2  │
                          │  released back     │
                          └────────────────────┘
```

### Check running jobs

```bash
curl -s localhost:9123/jobs | python -m json.tool
```

---

## Configuration

| Env Var | Default | Description |
|---------|---------|-------------|
| `GPUSCHED_PORT` | `9123` | Server listen port |
| `GPUSCHED_URL` | `http://localhost:9123` | Where `srun` connects |

---

## Files

| File | Lines | What it does |
|------|-------|-------------|
| `srun` | ~65 | Shell script — acquires GPUs, sets env, `exec`s your command |
| `server.py` | ~95 | HTTP server — FIFO queue, GPU dispatch, PID monitoring |
| `gpu.py` | ~35 | Wraps `nvidia-smi` to detect free/busy GPUs |
| `run_server.py` | 4 | Entry point |

---

## Slurm vs. local-gpu-scheduler

| | Slurm | This |
|---|---|---|
| Install time | 30+ min | 60 sec |
| Dependencies | munge, MySQL, slurmctld | Python 3, curl, jq |
| Config files | `slurm.conf` (100+ lines) | None |
| Root required | Usually | No |
| Multi-node | ✅ | ❌ Single machine only |
| Fair-share, priorities | ✅ | ❌ FIFO only |
| Best for | Clusters, 10+ users | 1 machine, small team |
