#!/usr/bin/env python3
"""TUI dashboard for the GPU scheduler — polls /status and /jobs."""
import curses, json, os, time, urllib.request

URL = os.environ.get("GPUSCHED_URL", "http://localhost:9123")

def _get(path):
    try:
        r = urllib.request.urlopen(f"{URL}{path}", timeout=2)
        return json.loads(r.read())
    except Exception:
        return None

def draw(stdscr):
    curses.curs_set(0)
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_RED, -1)
    curses.init_pair(4, curses.COLOR_CYAN, -1)
    curses.init_pair(5, curses.COLOR_MAGENTA, -1)
    stdscr.timeout(1000)  # refresh every 1s

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        status = _get("/status")
        jobs = _get("/jobs")

        # ── Header ────────────────────────────────────────
        if status:
            title = f" 🖥  local-gpu-scheduler v{status['version']}  |  :{status['port']}  |  up {_fmt_time(status['uptime_s'])} "
            stdscr.addnstr(0, 0, title, w, curses.A_BOLD | curses.color_pair(4))

            # ── GPU bar ───────────────────────────────────
            total = status["gpus_total"]
            alloc = status["gpus_allocated"]
            bar = ""
            for i in range(total):
                bar += "█" if i in alloc else "░"
            gpu_line = f" GPUs [{bar}]  {len(alloc)}/{total} allocated"
            stdscr.addnstr(2, 0, gpu_line, w, curses.A_BOLD)

            # ── Stats ─────────────────────────────────────
            stats = f" Running: {status['jobs_running']}  Queued: {status['jobs_queued']}  Total: {status['jobs_total']}"
            stdscr.addnstr(3, 0, stats, w, curses.color_pair(1))
        else:
            stdscr.addnstr(0, 0, " ⚠  Cannot reach scheduler — is the server running?", w, curses.A_BOLD | curses.color_pair(3))

        # ── Job table ─────────────────────────────────────
        y = 5
        if y < h:
            hdr = f" {'JOB_ID':<10} {'STATUS':<12} {'GPU':<10} {'PID':<8} {'COMMAND'}"
            stdscr.addnstr(y, 0, hdr, w, curses.A_BOLD | curses.A_UNDERLINE)
            y += 1

        if jobs:
            for j in jobs:
                if y >= h - 1:
                    break
                gpu_str = ",".join(map(str, j.get("gpus") or ["-"]))
                cmd = j.get("cmd", j.get("num_gpus", ""))
                line = f" {j['id']:<10} {j['status']:<12} {gpu_str:<10} {j['pid']:<8} {cmd}"
                color = {"running": 1, "queued": 2, "done": 4, "failed": 3, "cancelled": 5}.get(j["status"], 0)
                stdscr.addnstr(y, 0, line, w, curses.color_pair(color))
                y += 1
        elif jobs is not None:
            if y < h - 1:
                stdscr.addnstr(y, 0, "  (no jobs)", w, curses.A_DIM)

        # ── Footer ────────────────────────────────────────
        if h > 2:
            footer = " q: quit  |  refreshes every 1s"
            stdscr.addnstr(h - 1, 0, footer, w, curses.A_DIM)

        stdscr.refresh()

        key = stdscr.getch()
        if key in (ord('q'), ord('Q'), 27):
            break

def _fmt_time(s):
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"

if __name__ == "__main__":
    curses.wrapper(draw)
