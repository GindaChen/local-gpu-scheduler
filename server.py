"""Minimal GPU job scheduler server — stdlib only."""
import http.server, json, os, signal, threading, time, uuid

from gpu import get_free_gpu_indices

PORT = int(os.environ.get("GPUSCHED_PORT", 9123))

# ── Job store ──────────────────────────────────────────────────────────
lock = threading.Lock()
jobs = {}        # job_id -> {pid, gpus, num_gpus, status}
waiters = []     # [(event, request_dict)]  — threads waiting for GPUs
gpu_alloc = {}   # gpu_index -> job_id  — currently allocated GPUs

def _pid_alive(pid):
    """Check if a process is still running."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

# ── Scheduler loop ────────────────────────────────────────────────────
def scheduler_loop():
    while True:
        time.sleep(1)
        with lock:
            # 1. Reap finished jobs (PID exited)
            for jid, j in list(jobs.items()):
                if j["status"] == "running" and not _pid_alive(j["pid"]):
                    j["status"] = "done"
                    for g in j["gpus"]:
                        gpu_alloc.pop(g, None)

            # 2. Try to satisfy waiting requests (FIFO)
            free = get_free_gpu_indices()
            free = [g for g in free if g not in gpu_alloc]
            still_waiting = []
            for evt, req in waiters:
                n = req["num_gpus"]
                if len(free) >= n:
                    assigned = free[:n]
                    free = free[n:]
                    jid = uuid.uuid4().hex[:8]
                    jobs[jid] = {"pid": req["pid"], "gpus": assigned,
                                 "num_gpus": n, "status": "running"}
                    for g in assigned:
                        gpu_alloc[g] = jid
                    req["result"] = {"job_id": jid, "gpus": ",".join(map(str, assigned))}
                    evt.set()
                else:
                    still_waiting.append((evt, req))
            waiters[:] = still_waiting

# ── HTTP handler ──────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):
    def _json(self, code, obj):
        body = json.dumps(obj, indent=2).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        return json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))

    def log_message(self, fmt, *args):
        pass  # silence per-request logs

    def do_GET(self):
        if self.path == "/jobs":
            with lock:
                self._json(200, [{"id": jid, **{k: v for k, v in j.items() if k != "pid"},
                                   "pid": j["pid"]} for jid, j in jobs.items()])
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        data = self._body()
        if self.path == "/acquire":
            pid = data["pid"]
            num_gpus = data.get("num_gpus", 1)
            evt = threading.Event()
            req = {"pid": pid, "num_gpus": num_gpus, "result": None}
            with lock:
                waiters.append((evt, req))
            # Block until scheduler assigns GPUs
            evt.wait()
            self._json(200, req["result"])
        else:
            self._json(404, {"error": "not found"})

def serve():
    s = http.server.HTTPServer(("", PORT), Handler)
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    print(f"gpusched server on :{PORT}")
    s.serve_forever()

if __name__ == "__main__":
    serve()
