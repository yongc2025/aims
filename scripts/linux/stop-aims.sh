#!/usr/bin/env bash
# AIMS stop script for Ubuntu/Linux
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PID_FILE="$ROOT/runtime/aims.pid"
PORTS=(18765)
STOPPED=false

echo "Searching for AIMS processes..."

# --- Method 1: Find by listening port ---
for PORT in "${PORTS[@]}"; do
    PIDS=()
    if command -v ss &>/dev/null; then
        PIDS=($(ss -tlnp "sport = :$PORT" 2>/dev/null | grep -oP 'pid=\K\d+' || true))
    elif command -v lsof &>/dev/null; then
        PIDS=($(lsof -ti ":$PORT" -P -n 2>/dev/null || true))
    elif command -v fuser &>/dev/null; then
        PIDS=($(fuser "$PORT/tcp" 2>/dev/null || true))
    fi

    for PID in "${PIDS[@]}"; do
        if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
            # Verify it's an AIMS-related process
            CMD="$(ps -p "$PID" -o command= 2>/dev/null || true)"
            if echo "$CMD" | grep -qE "backend\.main|uvicorn"; then
                echo "Stopping AIMS process $PID (port $PORT)..."
                kill "$PID" 2>/dev/null || true
                sleep 1
                # Force kill if still running
                kill -9 "$PID" 2>/dev/null || true
                STOPPED=true
            fi
        fi
    done
done

# --- Method 2: Try PID file ---
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "Stopping AIMS process $PID (from PID file)..."
        kill "$PID" 2>/dev/null || true
        sleep 1
        kill -9 "$PID" 2>/dev/null || true
        STOPPED=true
    fi
    rm -f "$PID_FILE"
fi

if [ "$STOPPED" = true ]; then
    echo "AIMS stopped."
else
    echo "No AIMS process found."
fi
