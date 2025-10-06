import subprocess
import time
import os
import datetime
import signal
import sys

# ===== CONFIGURATION =====
TUNNEL_NAME = "mytunnel"   # Change this to your Cloudflare tunnel name
LOG_FILE = "tunnel_log.txt"
REFRESH_INTERVAL = 60      # Restart every 60 seconds
LOCK_FILE = "/tmp/keep_tunnel_alive.lock"


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

                if time.time() - start_time >= REFRESH_INTERVAL:
                    log("Refreshing Cloudflare Tunnel...")
                    process.terminate()
                    process.wait(timeout=10)
                    break
            time.sleep(3)
        except Exception as e:
            log(f"[ERROR] {e}")
            time.sleep(5)


def start_background():
    """Launch this script in the background."""
    log("Launching background process...")
    cmd = f"nohup python3 {os.path.abspath(sys.argv[0])} --auto > output.log 2>&1 &"
    subprocess.call(cmd, shell=True)
    log("Background process started successfully.")


def add_autostart():
    """Add this script to .bashrc so it runs on workspace start."""
    home = os.path.expanduser("~")
    bashrc = os.path.join(home, ".bashrc")
    autoline = f"nohup python3 {os.path.abspath(sys.argv[0])} --auto > /dev/null 2>&1 &\n"
    with open(bashrc, "r+") as f:
        lines = f.readlines()
        if autoline not in lines:
            f.write(f"\n# Auto-start Cloudflare keep-alive\n{autoline}")
            log("Added auto-start entry to .bashrc.")
        else:
            log("Auto-start entry already exists in .bashrc.")


def already_running():
    """Prevent duplicate instances."""
    if os.path.exists(LOCK_FILE):
        with open(LOCK_FILE) as f:
            pid = f.read().strip()
        if pid and os.path.exists(f"/proc/{pid}"):
            log(f"Process already running with PID {pid}. Exiting.")
            return True
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return False


if __name__ == "__main__":
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()

    if "--auto" in sys.argv:
        if already_running():
            sys.exit(0)
        run_forever()
        sys.exit(0)

    print("\n✅ Cloudflare Tunnel Auto-Runner")
    print("This will keep your tunnel alive 24/7, even after restart.\n")
    choice = input("Enable persistent mode? (y/n): ").strip().lower()

    if choice == "y":
        log("User chose YES — enabling persistent mode and autostart.")
        add_autostart()
        start_background()
        print("\n✅ Running 24/7 in background and will auto-relaunch after restart!")
        print("   To check logs: tail -f tunnel_log.txt\n")
    else:
        log("User chose NO — exiting.")
        print("Exited. Persistent mode not enabled.")
