# cyberkidflow.py
import subprocess
import threading
import time
import requests
import os
import sys
import json

# === CONFIG ===
SERVER_EXE = os.getenv("SERVER_EXE")
SERVER_PORT = int(os.getenv("SERVER_PORT", "8000"))
TUNNEL_URL_FILE = os.getenv("TUNNEL_URL_FILE", "tunnel_url.txt")
CLOUDFLARED_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

def log(msg): print(f"[CyberkidFlow] {msg}")

def start_server():
    log(f"Starting server: {SERVER_EXE}")
    return subprocess.Popen(
        [SERVER_EXE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

def start_cloudflared(port):
    log("Downloading cloudflared...")
    import urllib.request
    urllib.request.urlretrieve(CLOUDFLARED_URL, "cloudflared.exe")

    log(f"Starting tunnel to localhost:{port}")
    return subprocess.Popen(
        ["cloudflared.exe", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

def stream_logs(name, proc):
    for line in proc.stdout:
        print(f"[{name}] {line.rstrip()}")

def wait_for_port(port, timeout=120):
    log(f"Waiting for port {port}...")
    import socket
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket() as s:
            try:
                s.connect(("127.0.0.1", port))
                log(f"Port {port} is OPEN")
                return True
            except:
                time.sleep(1)
    log(f"Port {port} never opened")
    return False

def wait_for_health(url, timeout=30):
    log(f"Waiting for health at {url}")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3)
            if r.status_code == 200:
                log("Health check PASSED")
                return True
        except:
            time.sleep(1)
    log("Health check FAILED")
    return False

def get_tunnel_url(tunnel_proc, timeout=60):
    log("Waiting for Cloudflare tunnel URL...")
    start = time.time()
    while time.time() - start < timeout:
        line = tunnel_proc.stdout.readline()
        if not line:
            time.sleep(1)
            continue
        print(f"[tunnel] {line.rstrip()}")
        if "https://" in line and "trycloudflare.com" in line:
            url = line.strip().split("https://")[-1].split()[0]
            url = "https://" + url
            with open(TUNNEL_URL_FILE, "w") as f:
                f.write(url)
            log(f"TUNNEL READY: {url}")
            return url
    return None

# === CYBERKIDFLOW EXECUTION ===
if __name__ == "__main__":
    if not os.path.exists(SERVER_EXE):
        log(f"Server not found: {SERVER_EXE}")
        sys.exit(1)

    # 1. Start server
    server = start_server()
    threading.Thread(target=stream_logs, args=("SERVER", server), daemon=True).start()

    # 2. Wait for port
    if not wait_for_port(SERVER_PORT):
        server.terminate()
        sys.exit(1)

    # 3. Start Cloudflare tunnel
    tunnel = start_cloudflared(SERVER_PORT)
    threading.Thread(target=stream_logs, args=("TUNNEL", tunnel), daemon=True).start()

    # 4. Get public URL
    public_url = get_tunnel_url(tunnel)
    if not public_url:
        log("Failed to get tunnel URL")
        server.terminate()
        tunnel.terminate()
        sys.exit(1)

    # 5. Health check via tunnel
    if not wait_for_health(f"{public_url}/health", timeout=30):
        log("Remote health check failed")
        # Optional: still continue or fail
        # sys.exit(1)

    # 6. Run client tests (example)
    try:
        r = requests.get(public_url, timeout=10)
        assert r.status_code == 200
        log("Client test PASSED")
    except Exception as e:
        log(f"Client test FAILED: {e}")
        # sys.exit(1)  # optional

    # 7. Keep alive (CI will kill after step)
    log("CyberkidFlow complete. Server and tunnel running.")
    log(f"Public URL saved to {TUNNEL_URL_FILE}")

    # Keep script alive until CI timeout
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        server.terminate()
        tunnel.terminate()
        try: server.wait(5); tunnel.wait(5)
        except: server.kill(); tunnel.kill()
