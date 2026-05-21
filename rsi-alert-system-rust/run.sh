#!/usr/bin/env bash
set -euo pipefail

# RSI Alert System — run script
# Usage: ./run.sh [--dev]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUSTUP_DIR="$HOME/.rustup/toolchains/stable-x86_64-unknown-linux-gnu"

# Ensure rustup toolchain (rustc 1.95) is used instead of system rustc (1.75)
export PATH="$RUSTUP_DIR/bin:$PATH"

cd "$SCRIPT_DIR"

if [ "${1:-}" = "--dev" ]; then
    echo "Starting in dev mode (cargo run)..."
    cargo run
else
    echo "Building release binary..."
    cargo build --release
    echo "Starting RSI Alert System..."
    echo "Dashboard: http://127.0.0.1:3000"
    exec ./target/release/rsi-alert-system
fi
