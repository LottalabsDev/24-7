import subprocess
import time
import datetime
import os

# ==== CONFIGURATION ====
# Replace this with the command to start your IDX workspace
# For example, "bash start-workspace.sh" or "python3 main.py"
COMMAND = "bash start-workspace.sh"

# Optional: path for logs
LOG_FILE = "workspace_log.txt"

# ==== MAIN LOOP ====
def log(msg):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def run_forever():
    log("=== IDX 24/7 Workspace Keeper Started ===")
    while True:
        log(f"Starting process: {COMMAND}")
        try:
            # Start the process
            process = subprocess.Popen(COMMAND, shell=True)
            # Wait until it exits
            process.wait()
            code = process.returncode
            log(f"Process exited with code {code}")
        except Exception as e:
            log(f"Error running command: {e}")
        # Wait a few seconds before restarting
        log("Restarting in 5 seconds...")
        time.sleep(5)

if __name__ == "__main__":
    # Make sure log file exists
    if not os.path.exists(LOG_FILE):
        open(LOG_FILE, "w").close()
    run_forever()
