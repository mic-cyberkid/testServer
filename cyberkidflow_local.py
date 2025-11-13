# cyberkidflow_local.py
import subprocess
import threading
import time
import socket
import sys
import os

# === CONFIG ===
SERVER_EXE = os.getenv("SERVER_EXE")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
TEST_SCRIPT = os.getenv("TEST_SCRIPT", "test_all.py")

def log(msg): print(f"[CyberkidFlow] {msg}")

def start_server():
    if not os.path.exists(SERVER_EXE):
        log(f"SERVER NOT FOUND: {SERVER_EXE}")
        sys.exit(1)
    log(f"Starting server: {SERVER_EXE}")
    return subprocess.Popen(
        [SERVER_EXE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

def stream_logs(name, proc):
    for line in iter(proc.stdout.readline, ''):
        if line:
            print(f"[{name}] {line.rstrip()}")

def wait_for_port(port, timeout=120):
    log(f"Waiting for localhost:{port}...")
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect(("127.0.0.1", port))
                log(f"Port {port} is OPEN")
                return True
            except:
                time.sleep(1)
    log(f"Port {port} never opened")
    return False

# === CYBERKIDFLOW EXECUTION ===
if __name__ == "__main__":
    # 1. Start server
    server = start_server()
    threading.Thread(target=stream_logs, args=("SERVER", server), daemon=True).start()
    # intentional delay
    time.sleep(30)

    # 2. Wait for port
    if not wait_for_port(SERVER_PORT):
        server.terminate()
        sys.exit(1)

    # 3. Run test_all.py
    log(f"Running test script: {TEST_SCRIPT}")
    try:
        result = subprocess.run(
            [sys.executable, TEST_SCRIPT],
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        log("test_all.py PASSED")
    except subprocess.CalledProcessError as e:
        print(e.stdout)
        print(e.stderr)
        log("test_all.py FAILED")
        server.terminate()
        sys.exit(1)

    # 4. Clean shutdown
    log("Shutting down server...")
    server.terminate()
    try:
        server.wait(timeout=10)
    except:
        server.kill()
    log("CyberkidFlow complete.")
