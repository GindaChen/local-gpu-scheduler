"""Minimal GPU job scheduler server — stdlib only."""
import http.server, json, os, socket, socketserver, threading, time, uuid

from gpu import get_all_gpus, get_free_gpu_indices

PORT = int(os.environ.get("GPUSCHED_PORT", 9123))
START_TIME = time.time()

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
            # Drop queued requests whose PID has already exited
            alive_waiters = []
            for evt, req in waiters:
                if _pid_alive(req["pid"]):
                    alive_waiters.append((evt, req))
                else:
                    # Unblock any thread waiting on this request; don't assign GPUs to dead PIDs
                    req["result"] = {"error": "pid not alive"}
                    evt.set()
            waiters[:] = alive_waiters

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
        """Parse JSON body; on error send 400 and return None."""
        try:
            cl = self.headers.get("Content-Length")
            if cl is None or cl == "":
                self._json(400, {"error": "missing Content-Length"})
                return None
            n = int(cl)
            if n < 0:
                self._json(400, {"error": "invalid Content-Length"})
                return None
            raw = self.rfile.read(n)
            if not raw:
                self._json(400, {"error": "empty body"})
                return None
            return json.loads(raw)
        except ValueError:
            self._json(400, {"error": "invalid Content-Length"})
            return None
        except json.JSONDecodeError as e:
            self._json(400, {"error": f"invalid JSON: {e}"})
            return None

    def log_message(self, fmt, *args):
        pass  # silence per-request logs

    def do_GET(self):
        if self.path == "/status":
            with lock:
                running = [j for j in jobs.values() if j["status"] == "running"]
                self._json(200, {
                    "service": "local-gpu-scheduler",
                    "version": "0.1.0",
                    "uptime_s": round(time.time() - START_TIME),
                    "port": PORT,
                    "gpus_total": len(get_all_gpus()),
                    "gpus_allocated": list(gpu_alloc.keys()),
                    "jobs_running": len(running),
                    "jobs_queued": len(waiters),
                    "jobs_total": len(jobs),
                })
        elif self.path == "/jobs":
            with lock:
                self._json(200, [{"id": jid, **{k: v for k, v in j.items() if k != "pid"},
                                   "pid": j["pid"]} for jid, j in jobs.items()])
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        data = self._body()
        if data is None:
            return
        if self.path == "/acquire":
            pid = data["pid"]
            num_gpus = data.get("num_gpus", 1)
            if num_gpus < 0:
                self._json(400, {"error": "num_gpus cannot be negative"})
                return
            total_gpus = len(get_all_gpus())
            if num_gpus > total_gpus:
                self._json(400, {
                    "error": f"requested {num_gpus} GPU(s) but only {total_gpus} available on this machine"
                })
                return
            evt = threading.Event()
            req = {"pid": pid, "num_gpus": num_gpus, "result": None}
            with lock:
                waiters.append((evt, req))
            # Wait for GPUs; periodically check if client disconnected (e.g. remote client or connection drop)
            while not evt.is_set():
                evt.wait(timeout=1)
                if evt.is_set():
                    break
                try:
                    self.connection.setblocking(False)
                    try:
                        peek = self.connection.recv(1, socket.MSG_PEEK)
                    finally:
                        self.connection.setblocking(True)
                    if peek == b"":
                        raise ConnectionError("closed")
                except BlockingIOError:
                    pass  # no data yet, connection still open
                except (BrokenPipeError, ConnectionResetError, OSError, ConnectionError):
                    with lock:
                        waiters[:] = [(e, r) for (e, r) in waiters if (e, r) != (evt, req)]
                    return
            self._json(200, req["result"])
        else:
            self._json(404, {"error": "not found"})

def serve():
    class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        pass
    s = ThreadedHTTPServer(("", PORT), Handler)
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    print(f"gpusched server on :{PORT}")
    s.serve_forever()

if __name__ == "__main__":
    serve()
