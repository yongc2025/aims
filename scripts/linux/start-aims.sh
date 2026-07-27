#!/usr/bin/env bash
# AIMS startup script for Ubuntu/Linux
# Note: logs/aims.log uses RotatingFileHandler (10MB, 5 backups).
# stdout/stderr redirects here do NOT auto-rotate.
# For production, prefer systemd (aims.service → journald) or set up logrotate:
#   sudo cp scripts/linux/logrotate-aims.conf /etc/logrotate.d/aims
set -euo pipefail

PORT="${1:-18765}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUNTIME_DIR="$ROOT/runtime"
LOGS_DIR="$ROOT/logs"
PID_FILE="$RUNTIME_DIR/aims.pid"

mkdir -p "$RUNTIME_DIR" "$LOGS_DIR"

# Clear proxy environment variables to avoid accidental routing
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy

# --- Helper: check if a port is already in use ---
port_in_use() {
    local port="$1"
    if command -v ss &>/dev/null; then
        ss -tlnp "sport = :$port" 2>/dev/null | grep -q LISTEN
    elif command -v lsof &>/dev/null; then
        lsof -i ":$port" -P -n 2>/dev/null | grep -q LISTEN
    else
        # fallback: try connecting
        (echo >/dev/tcp/127.0.0.1/"$port") 2>/dev/null
    fi
}

# --- Check if already running via PID file ---
if [ -f "$PID_FILE" ]; then
    EXISTING_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$EXISTING_PID" ] && kill -0 "$EXISTING_PID" 2>/dev/null; then
        echo "AIMS is already running (PID $EXISTING_PID)."
        echo "Visit http://127.0.0.1:$PORT/"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

# --- Check if port is already in use ---
if port_in_use "$PORT"; then
    echo "Port $PORT is already in use. If it's an AIMS process, run stop.sh first."
    exit 1
fi

# --- Find Python ---
# Priority: conda active env > conda 'py3127' env > .venv > system python
PYTHON=""

# 1. Check if we're already inside an active conda environment
if [ -n "${CONDA_PREFIX:-}" ] && [ -x "$CONDA_PREFIX/bin/python" ]; then
    PYTHON="$CONDA_PREFIX/bin/python"
    echo "Using active conda environment: $CONDA_PREFIX"
fi

# 2. Check for a conda environment named 'py3127' (or 'aims' as fallback)
if [ -z "$PYTHON" ] && command -v conda &>/dev/null; then
    for ENV_NAME in py3127 aims; do
        CONDAPY="$(conda run -n "$ENV_NAME" which python 2>/dev/null || echo "")"
        if [ -n "$CONDAPY" ] && [ -x "$CONDAPY" ]; then
            PYTHON="$CONDAPY"
            echo "Using conda environment: $ENV_NAME"
            break
        fi
    done
fi

# 3. Check for .venv (venv / virtualenv)
if [ -z "$PYTHON" ] && [ -f "$ROOT/.venv/bin/python" ]; then
    PYTHON="$ROOT/.venv/bin/python"
    echo "Using .venv: $ROOT/.venv"
fi

# 4. Fallback to system Python
if [ -z "$PYTHON" ]; then
    if command -v python3 &>/dev/null; then
        PYTHON="$(command -v python3)"
    elif command -v python &>/dev/null; then
        PYTHON="$(command -v python)"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "Python 3.11+ was not found. Please install conda env, create .venv, or install system Python."
    exit 1
fi

# --- Check Python version ---
PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [ "$(echo "$PY_VER" | cut -d. -f1)" -lt 3 ] || { [ "$(echo "$PY_VER" | cut -d. -f1)" -eq 3 ] && [ "$(echo "$PY_VER" | cut -d. -f2)" -lt 11 ]; }; then
    echo "Python 3.11+ required, found $PY_VER"
    exit 1
fi

# --- Initialize database ---
echo "Initializing database..."
"$PYTHON" -c "from backend.storage.database import init_database; init_database()"

# --- Start uvicorn in background ---
STDOUT_LOG="$LOGS_DIR/aims.stdout.log"
STDERR_LOG="$LOGS_DIR/aims.stderr.log"
AIMS_LOG="$LOGS_DIR/aims.log"

export AIMS_LOG_FILE="$AIMS_LOG"

echo "Starting AIMS on port $PORT..."
cd "$ROOT"

nohup "$PYTHON" -m uvicorn backend.main:app \
    --host 127.0.0.1 \
    --port "$PORT" \
    >> "$STDOUT_LOG" 2>> "$STDERR_LOG" &

AIMS_PID=$!
echo "$AIMS_PID" > "$PID_FILE"

# Wait briefly and check if the process is still alive
sleep 2
if kill -0 "$AIMS_PID" 2>/dev/null; then
    echo "AIMS started successfully (PID $AIMS_PID)."
    echo "Internal (localhost only): http://127.0.0.1:$PORT/"
    echo "Logs: $LOGS_DIR"
else
    echo "AIMS failed to start. Check logs: $STDERR_LOG"
    cat "$STDERR_LOG" 2>/dev/null | tail -20
    rm -f "$PID_FILE"
    exit 1
fi
