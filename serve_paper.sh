#!/bin/bash
set -euo pipefail

PORT=8899
SERVE_DIR="${PAPER_SERVE_DIR:-$HOME/newspaper_out}"

if [ $# -ne 1 ]; then
    echo "usage: ./serve_paper.sh <run_dir>" >&2
    exit 1
fi

RUN_DIR="${1%/}"
PAGE="$RUN_DIR/paper/index.html"

if [ ! -f "$PAGE" ]; then
    echo "serve_paper: no page at $PAGE (run build_newspaper.py first)" >&2
    exit 1
fi

mkdir -p "$SERVE_DIR"
cp "$PAGE" "$SERVE_DIR/index.html"

if ! ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    setsid nohup python3 -m http.server "$PORT" --bind 0.0.0.0 --directory "$SERVE_DIR" \
        > "$SERVE_DIR/http.log" 2>&1 < /dev/null &
    for _ in 1 2 3 4 5 6 7 8 9 10; do
        ss -ltn 2>/dev/null | grep -q ":$PORT " && break
        sleep 0.3
    done
fi

if ! ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    echo "serve_paper: the server did not come up on port $PORT" >&2
    exit 1
fi

TS_IP="$(tailscale ip -4 2>/dev/null | head -1 || true)"

if [ -z "$TS_IP" ]; then
    echo "serve_paper: no tailnet address from 'tailscale ip -4'" >&2
    echo "http://127.0.0.1:$PORT/"
    exit 1
fi

echo "http://$TS_IP:$PORT/"
