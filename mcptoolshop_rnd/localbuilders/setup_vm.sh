#!/usr/bin/env bash
# Colab VM containment setup for local-builders J2 (amendment C, F9).
set -euo pipefail

BUILDER_USER="${BUILDER_USER:-builder}"
PROXY_PORT="${PROXY_PORT:-18080}"
LLAMA_PORT="${LLAMA_PORT:-18081}"
BANK_DIR="${BANK_DIR:-/root/j2/bank}"
TWINS_DIR="${TWINS_DIR:-/root/j2/twins}"
RECEIPTS_DIR="${RECEIPTS_DIR:-/root/j2/receipts}"

# 1. Refuse if Google Drive is mounted on the VM.
if grep -qiE '/content/drive|/content/gdrive|fuse\.drive' /proc/mounts 2>/dev/null; then
  echo "FATAL: Google Drive is mounted on this VM; refusing to proceed." >&2
  exit 1
fi
if [ -d /content/drive ] && [ -n "$(ls -A /content/drive 2>/dev/null)" ]; then
  echo "FATAL: /content/drive is non-empty; refusing to proceed." >&2
  exit 1
fi

# 2. Create the unprivileged builder user if missing.
if ! id -u "$BUILDER_USER" >/dev/null 2>&1; then
  useradd --system --no-create-home --shell /bin/sh "$BUILDER_USER"
fi

# 3. Lock task bank, held-out twins, and receipts directories to root:root 0700.
mkdir -p "$BANK_DIR" "$TWINS_DIR" "$RECEIPTS_DIR"
chown root:root "$BANK_DIR" "$TWINS_DIR" "$RECEIPTS_DIR"
chmod 0700 "$BANK_DIR" "$TWINS_DIR" "$RECEIPTS_DIR"

# 4. Apply iptables and ip6tables owner rules for builder:
#    allow TCP only to 127.0.0.1:$PROXY_PORT; reject llama-server, DNS, and internet.
iptables -A OUTPUT -p tcp -d 127.0.0.1 --dport "$LLAMA_PORT" -m owner --uid-owner "$BUILDER_USER" -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -p udp --dport 53 -m owner --uid-owner "$BUILDER_USER" -j REJECT
iptables -A OUTPUT -p tcp --dport 53 -m owner --uid-owner "$BUILDER_USER" -j REJECT --reject-with tcp-reset
iptables -A OUTPUT -p tcp -d 127.0.0.1 --dport "$PROXY_PORT" -m owner --uid-owner "$BUILDER_USER" -j ACCEPT
iptables -A OUTPUT -m owner --uid-owner "$BUILDER_USER" -j REJECT
ip6tables -A OUTPUT -m owner --uid-owner "$BUILDER_USER" -j REJECT

# 5. Export offline environment defaults.
export LITELLM_LOCAL_MODEL_COST_MAP=True
export PIP_NO_INDEX=1
export NPM_CONFIG_OFFLINE=true
export GIT_CONFIG_NOSYSTEM=1
