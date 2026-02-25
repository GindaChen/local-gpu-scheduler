"""Tests for the GPU scheduler (no real GPU required)."""
import json, os, threading, time, unittest, urllib.request
from unittest.mock import patch, MagicMock
from http.server import HTTPServer

import gpu, server

# ── GPU detection tests ────────────────────────────────────────────────
FAKE_QUERY_GPU = "0, GPU-aaa, NVIDIA A100, 40960\n1, GPU-bbb, NVIDIA A100, 40960\n"
FAKE_COMPUTE_APPS = "GPU-aaa\n"
FAKE_COMPUTE_APPS_EMPTY = ""

def fake_smi_factory(query_gpu_out, compute_apps_out):
    def fake_run(cmd, **kw):
        m = MagicMock()
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
        if "--query-gpu" in cmd_str:
            m.stdout = query_gpu_out
        elif "--query-compute-apps" in cmd_str:
            m.stdout = compute_apps_out
        else:
            m.stdout = ""
        return m
    return fake_run

class TestGPU(unittest.TestCase):
    @patch("gpu.subprocess.run", side_effect=fake_smi_factory(FAKE_QUERY_GPU, FAKE_COMPUTE_APPS))
    def test_all_gpus(self, _):
        gpus = gpu.get_all_gpus()
        self.assertEqual(len(gpus), 2)

    @patch("gpu.subprocess.run", side_effect=fake_smi_factory(FAKE_QUERY_GPU, FAKE_COMPUTE_APPS))
    def test_busy(self, _):
        self.assertEqual(gpu.get_busy_gpu_indices(), {0})

    @patch("gpu.subprocess.run", side_effect=fake_smi_factory(FAKE_QUERY_GPU, FAKE_COMPUTE_APPS))
    def test_free(self, _):
        self.assertEqual(gpu.get_free_gpu_indices(), [1])

    @patch("gpu.subprocess.run", side_effect=fake_smi_factory(FAKE_QUERY_GPU, FAKE_COMPUTE_APPS_EMPTY))
    def test_all_free(self, _):
        self.assertEqual(gpu.get_free_gpu_indices(), [0, 1])

# ── Server tests ──────────────────────────────────────────────────────
def _req(method, path, data=None, port=None):
    url = f"http://localhost:{port}{path}"
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body, method=method,
                               headers={"Content-Type": "application/json"} if body else {})
    return json.loads(urllib.request.urlopen(r).read())

class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 19876
        server.PORT = cls.port
        server.jobs.clear()
        server.waiters.clear()
        server.gpu_alloc.clear()
        cls.httpd = HTTPServer(("", cls.port), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        # Start scheduler loop with mocked GPUs
        cls.sched = threading.Thread(target=server.scheduler_loop, daemon=True)
        cls.sched.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()

    @patch("server.get_free_gpu_indices", return_value=[0, 1])
    def test_acquire_returns_gpus(self, _):
        """Acquire should block until GPUs assigned, then return them."""
        pid = os.getpid()  # use our own PID (it's alive)
        r = _req("POST", "/acquire", {"pid": pid, "num_gpus": 1}, self.port)
        self.assertIn("gpus", r)
        self.assertIn("job_id", r)
        self.assertIn(r["gpus"], ["0", "1"])

    @patch("server.get_free_gpu_indices", return_value=[0, 1])
    def test_jobs_list_shows_running(self, _):
        """After acquire, job should appear in /jobs as running."""
        pid = os.getpid()
        r = _req("POST", "/acquire", {"pid": pid, "num_gpus": 1}, self.port)
        jid = r["job_id"]
        jobs = _req("GET", "/jobs", port=self.port)
        match = [j for j in jobs if j["id"] == jid]
        self.assertTrue(match)
        self.assertEqual(match[0]["status"], "running")

    def test_jobs_endpoint(self):
        """Jobs endpoint returns a list."""
        r = _req("GET", "/jobs", port=self.port)
        self.assertIsInstance(r, list)

if __name__ == "__main__":
    unittest.main()
