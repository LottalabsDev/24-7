#!/usr/bin/env bash
# ======================================================
#  keepalive.sh — 24/7 self-monitoring + auto-restart
#  For idx.google.com or any Linux VPS
# ======================================================

# === CONFIGURATION ===
APP_COMMAND="bash /root/start.sh"        # Command to start your app
APP_PORT=3000                            # Port your app uses (for health check)
LOG_FILE="/root/keepalive.log"
MAX_LOG_SIZE=5242880                     # 5MB log rotation limit
CHECK_INTERVAL=30                        # Health check every 30 seconds
# === END CONFIG ===

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

rotate_logs() {
    if [ "$(stat -c%s "$LOG_FILE")" -ge "$MAX_LOG_SIZE" ]; then
        mv "$LOG_FILE" "${LOG_FILE}.1"
        echo "" > "$LOG_FILE"
        log "[INFO] Log rotated"
    fi
}

health_check() {
    if command -v curl >/dev/null 2>&1; then
        curl -fs "http://127.0.0.1:${APP_PORT}" >/dev/null 2>&1
        return $?
    else
        nc -z 127.0.0.1 "${APP_PORT}" >/dev/null 2>&1
        return $?
    fi
}

run_app() {
    log "[INFO] Launching main app..."
    eval "$APP_COMMAND" >> "$LOG_FILE" 2>&1 &
    APP_PID=$!
    log "[INFO] App started with PID $APP_PID"
}

monitor_app() {
    while true; do
        rotate_logs

        if ! ps -p "$APP_PID" > /dev/null 2>&1; then
            log "[WARN] App process not running — restarting..."
            run_app
        fi

        if ! health_check; then
            log "[WARN] Health check failed on port $APP_PORT — restarting app..."
            kill -9 "$APP_PID" >/dev/null 2>&1
            run_app
        fi

        # System info snapshot
        CPU=$(top -bn1 | awk '/Cpu/ {print $2"%"}' | head -n1)
        MEM=$(free -m | awk '/Mem:/ {print int($3/$2*100)"%"}')
        UPTIME=$(uptime -p)
        log "[HEALTH] CPU: $CPU | MEM: $MEM | UPTIME: $UPTIME"

        sleep "$CHECK_INTERVAL"
    done
}

# --- main ---
log "==============================================="
log "[BOOT] Starting keepalive system for $APP_COMMAND"
log "==============================================="

run_app
monitor_app
