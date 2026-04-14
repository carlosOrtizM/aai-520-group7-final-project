"""Launcher — spawns the FastHTML UI (:8010) and FastAPI agent (:8011).

Both subprocesses inherit stdout/stderr so logs land in the same
terminal. Ctrl+C terminates both gracefully. CWD is the project root
so the ``src`` package resolves correctly inside each child.
"""

import os
import subprocess
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")


def main():
    procs = []
    try:
        agent_proc = subprocess.Popen(
            [sys.executable, os.path.join(SRC_DIR, "agent", "app.py")],
            cwd=PROJECT_ROOT,
        )
        procs.append(agent_proc)
        print("[main] Agent service starting on http://localhost:8011")

        ui_proc = subprocess.Popen(
            [sys.executable, os.path.join(SRC_DIR, "ui", "app.py")],
            cwd=PROJECT_ROOT,
        )
        procs.append(ui_proc)
        print("[main] UI service starting on http://localhost:8010")

        for proc in procs:
            proc.wait()

    except KeyboardInterrupt:
        print("\n[main] Shutting down...")
        for proc in procs:
            proc.terminate()
        for proc in procs:
            proc.wait()
        print("[main] All services stopped.")


if __name__ == "__main__":
    main()
