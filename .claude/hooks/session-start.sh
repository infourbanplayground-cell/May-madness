#!/bin/bash
set -euo pipefail

# Only run in remote (cloud) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Urban Padel VPS: setting up SSH tunnel..."

# 1. Install openssh-client if missing
if ! command -v ssh &>/dev/null; then
  echo "==> Installing openssh-client..."
  apt-get install -y openssh-client -qq 2>&1
fi

# 2. Install SSH key from uploaded zip (if available) or from ~/.ssh if already there
KEY_PATH="$HOME/.ssh/urbanpadel-owner-key"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

if [ ! -f "$KEY_PATH" ]; then
  ZIP="/root/.claude/uploads/36ed82e5-2b0d-5c30-9ddd-aad5d04561ae/20008386-urbanpadelaccesskit.zip"
  if [ -f "$ZIP" ]; then
    echo "==> Extracting SSH key from kit zip..."
    unzip -p "$ZIP" urbanpadel-owner-key > "$KEY_PATH"
    chmod 600 "$KEY_PATH"
  else
    echo "ERROR: SSH key not found at $KEY_PATH and zip not found at $ZIP"
    echo "Please re-upload urbanpadel-access-kit.zip to continue."
    exit 1
  fi
fi
chmod 600 "$KEY_PATH"

# 3. Download chisel if not present
if [ ! -f /tmp/chisel ]; then
  echo "==> Downloading chisel..."
  curl -sL https://github.com/jpillora/chisel/releases/download/v1.10.1/chisel_1.10.1_linux_amd64.gz \
    | gunzip > /tmp/chisel && chmod +x /tmp/chisel
fi

# 4. Start tunnel (skip if already running)
if ! grep -q "Connected" /tmp/chisel.log 2>/dev/null; then
  echo "==> Starting chisel tunnel to sshws.urbanpadel.om..."
  /tmp/chisel client --keepalive 25s \
    --auth mouther:ca4ac97f11f618067ca6564606a226d8 \
    https://sshws.urbanpadel.om 2200:127.0.0.1:22 \
    > /tmp/chisel.log 2>&1 &
  sleep 4
fi

if ! grep -q "Connected" /tmp/chisel.log 2>/dev/null; then
  echo "ERROR: Chisel tunnel failed to connect. Log:"
  cat /tmp/chisel.log
  exit 1
fi
echo "==> Tunnel connected."

# 5. Write SSH config entry if not already present
SSH_CONFIG="$HOME/.ssh/config"
if ! grep -q "Host urbanpadel" "$SSH_CONFIG" 2>/dev/null; then
  cat >> "$SSH_CONFIG" << 'SSHEOF'

Host urbanpadel
  HostName 127.0.0.1
  Port 2200
  User root
  IdentityFile ~/.ssh/urbanpadel-owner-key
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  ServerAliveInterval 30
SSHEOF
  echo "==> SSH config written."
fi

echo "==> Urban Padel VPS ready. Run: ssh urbanpadel 'uptime'"
