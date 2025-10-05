import subprocess
import time
import datetime
import os
import signal
import sys

# ==== CONFIGURATION ====
# Replace this with the command to start your IDX workspace or process
COMMAND = "bash start-workspace.sh"  # Example startup command
LOG_FILE = "workspace_log.txt"

# ==== SIGNAL HANDLING ====
def handle_signal(signum, frame):
    log(f"Ignoring signal {signum} — keeping the process alive.")

# Ignore typical termination signals
for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
    signal.signal(sig, handle_signal)

# ==== LOGGING ====
def log(msg):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

# ==== MAIN LOOP ====
def run_forever():
    log("=== HyzexNodes 24/7 IDX Workspace Keeper Started ===")
    while True:
        try:
            log(f"Starting process: {COMMAND}")
            process = subprocess.Popen(
                COMMAND, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            # Continuously read and log output
            for line in iter(process.stdout.readline, b""):
                decoded = line.decode(errors="ignore").strip()
                if decoded:
                    log(f"[PROCESS] {decoded}")

            process.wait()
            code = process.returncode
            log(f"Process exited with code {code}. Restarting in 5 seconds...")
            time.sleep(5)

        except Exception as e:
            log(f"[ERROR] {e}")
            time.sleep(5)
            continue

if __name__ == "__main__":
    # Ensure log file exists
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()
    run_forever()
