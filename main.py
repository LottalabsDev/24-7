import subprocess
import time
import os
import datetime
import signal
import sys

# ===== CONFIGURATION =====
TUNNEL_NAME = "mytunnel"   # change this to your Cloudflare tunnel name
LOG_FILE = "tunnel_log.txt"
REFRESH_INTERVAL = 60      # restart every 1 minute

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

def run_command(cmd):
    """Run shell command and stream output to log."""
    log(f"Running command: {cmd}")
    process = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    for line in iter(process.stdout.readline, b""):
        decoded = line.decode(errors="ignore").strip()
        if decoded:
            log(decoded)
    process.wait()
    return process.returncode

def start_sshx():
    """Start SSHX.IO session first."""
    log("=== Starting SSHX.IO Session ===")
    try:
        cmd = "curl -sSf https://sshx.io/get | sh -s run"
        run_command(cmd)
        log("SSHX.IO session started successfully.")
    except Exception as e:
        log(f"[SSHX ERROR] {e}")

def run_forever():
    """Main loop to keep Cloudflare tunnel alive."""
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
    """Re-run this script in background using nohup (portable version)."""
    if "NOHUP_MODE" not in os.environ:
        log("Launching background process using nohup (portable mode)...")
        env = os.environ.copy()
        env["NOHUP_MODE"] = "1"
        cmd = f"nohup python3 {sys.argv[0]} > output.log 2>&1 &"
        subprocess.call(cmd, shell=True, env=env)
        log("Background process started successfully.")
        sys.exit(0)

if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    # Step 1: Start SSHX
    start_sshx()

    # Step 2: Ask user if they want 24/7 mode
    choice = input("Do you want to keep this workspace running 24/7? (y/n): ").strip().lower()

    if choice == "y":
        log("User chose YES — starting 24/7 Cloudflare tunnel mode.")
        ensure_background()
        run_forever()
    else:
        log("User chose NO — exiting.")
        print("Exited. The workspace will not run 24/7.")
        sys.exit(0)
