"""GPU detection via nvidia-smi.

Under the hood, this module runs two nvidia-smi commands:

1. List all GPUs:
   $ nvidia-smi --query-gpu=index,uuid,name,memory.total --format=csv,noheader,nounits
   Output:
     0, GPU-aaa-..., NVIDIA A100-SXM4-80GB, 81920
     1, GPU-bbb-..., NVIDIA A100-SXM4-80GB, 81920

2. List GPUs with active compute processes:
   $ nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader
   Output (one UUID per running process):
     GPU-aaa-...
     GPU-aaa-...

   If a GPU's UUID appears here, it's busy. Otherwise it's free.
"""
import subprocess, csv, io

def _run_smi(*args):
    """Run nvidia-smi with the given args and return stdout."""
    r = subprocess.run(["nvidia-smi", *args], capture_output=True, text=True)
    return r.stdout.strip()

def get_all_gpus():
    """Return list of {index, uuid, name, memory_mb} for each GPU.

    Runs: nvidia-smi --query-gpu=index,uuid,name,memory.total --format=csv,noheader,nounits
    """
    out = _run_smi("--query-gpu=index,uuid,name,memory.total", "--format=csv,noheader,nounits")
    if not out:
        return []
    gpus = []
    for row in csv.reader(io.StringIO(out)):
        row = [c.strip() for c in row]
        gpus.append({"index": int(row[0]), "uuid": row[1], "name": row[2], "memory_mb": int(row[3])})
    return gpus

def get_busy_gpu_indices():
    """Return set of GPU indices that have compute processes running.

    Runs: nvidia-smi --query-compute-apps=gpu_uuid --format=csv,noheader
    Cross-references UUIDs against get_all_gpus() to map back to indices.
    """
    gpus = get_all_gpus()
    uuid_to_idx = {g["uuid"]: g["index"] for g in gpus}
    out = _run_smi("--query-compute-apps=gpu_uuid", "--format=csv,noheader")
    if not out:
        return set()
    busy = set()
    for line in out.strip().splitlines():
        uuid = line.strip()
        if uuid in uuid_to_idx:
            busy.add(uuid_to_idx[uuid])
    return busy

def get_free_gpu_indices():
    """Return sorted list of GPU indices with no compute processes."""
    all_idx = {g["index"] for g in get_all_gpus()}
    return sorted(all_idx - get_busy_gpu_indices())
