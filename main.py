import subprocess
import time
import os
import datetime
import signal
import sys

# ===== CONFIGURATION =====
TUNNEL_NAME = "mytunnel"  # change this to your tunnel name
LOG_FILE = "tunnel_log.txt"
REFRESH_INTERVAL = 60  # restart every 1 minute

def log(msg):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def handle_signal(signum, frame):
    log(f"Ignoring signal {signum} — keeping the tunnel alive.")

for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
    signal.signal(sig, handle_signal)

def run_forever():
    log("=== Cloudflare Tunnel Auto-Keeper Started ===")
    while True:
        try:
            cmd = f"cloudflared tunnel run {TUNNEL_NAME}"
            log(f"Starting: {cmd}")
            process = subprocess.Popen(
                cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            start_time = time.time()
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                decoded = line.decode(errors="ignore").strip()
                if decoded:
                    log(f"[TUNNEL] {decoded}")

                # restart every 1 minute
                if time.time() - start_time >= REFRESH_INTERVAL:
                    log("Refreshing Cloudflare Tunnel...")
                    process.terminate()
                    process.wait(timeout=10)
                    break

            time.sleep(3)
        except Exception as e:
            log(f"[ERROR] {e}")
            time.sleep(5)

def ensure_background():
    """Re-run this script in background using nohup if not already detached."""
    if "NOHUP_MODE" not in os.environ:
        log("Launching background process using nohup...")
        cmd = f"nohup python3 {sys.argv[0]} > output.log 2>&1 & disown"
        subprocess.call(cmd, shell=True)
        log("Background process started successfully.")
        sys.exit(0)

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()
    ensure_background()
    run_forever()
