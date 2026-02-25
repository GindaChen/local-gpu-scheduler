"""GPU detection via nvidia-smi."""
import subprocess, csv, io

def _run_smi(*args):
    r = subprocess.run(["nvidia-smi", *args], capture_output=True, text=True)
    return r.stdout.strip()

def get_all_gpus():
    """Return list of {index, uuid, name, memory_mb} for each GPU."""
    out = _run_smi("--query-gpu=index,uuid,name,memory.total", "--format=csv,noheader,nounits")
    if not out:
        return []
    gpus = []
    for row in csv.reader(io.StringIO(out)):
        row = [c.strip() for c in row]
        gpus.append({"index": int(row[0]), "uuid": row[1], "name": row[2], "memory_mb": int(row[3])})
    return gpus

def get_busy_gpu_indices():
    """Return set of GPU indices that have compute processes running."""
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
