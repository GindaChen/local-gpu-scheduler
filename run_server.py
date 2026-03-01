#!/usr/bin/env python3
"""Start the GPU scheduler server."""
import argparse, os, sys

def main():
    p = argparse.ArgumentParser(description="GPU scheduler server")
    p.add_argument("-d", "--detach", action="store_true", help="Run server in background (daemon)")
    p.add_argument("--port", type=int, default=None, help="Override GPUSCHED_PORT")
    args = p.parse_args()

    if args.port:
        os.environ["GPUSCHED_PORT"] = str(args.port)

    if args.detach:
        pid = os.fork()
        if pid > 0:
            print(f"gpusched daemon started (pid={pid})")
            sys.exit(0)
        # Child: detach from terminal
        os.setsid()
        sys.stdin.close()
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        log = open(os.path.join(log_dir, "server.log"), "a")
        os.dup2(log.fileno(), 1)
        os.dup2(log.fileno(), 2)

    from server import serve
    serve()

if __name__ == "__main__":
    main()
