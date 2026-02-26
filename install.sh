#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
#  Install local-gpu-scheduler
#  Usage: curl -sSL https://raw.githubusercontent.com/GindaChen/local-gpu-scheduler/main/install.sh | bash
# ─────────────────────────────────────────────────────────────
set -euo pipefail

REPO="https://github.com/GindaChen/local-gpu-scheduler.git"
INSTALL_DIR="${HOME}/.local/share/gpu-scheduler"

echo "🚀 Installing local-gpu-scheduler..."

# Dependencies check
for cmd in python3 curl git; do
  command -v "$cmd" &>/dev/null || { echo "❌ '$cmd' is required but not found."; exit 1; }
done

if ! command -v jq &>/dev/null; then
  echo "⚠️  'jq' not found. Installing..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get install -y jq
  elif command -v brew &>/dev/null; then
    brew install jq
  else
    echo "❌ Cannot auto-install jq. Please install it manually."; exit 1
  fi
fi

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
  echo "📦 Updating existing installation..."
  git -C "$INSTALL_DIR" pull --quiet
else
  echo "📦 Cloning repository..."
  git clone --quiet "$REPO" "$INSTALL_DIR"
fi

chmod +x "$INSTALL_DIR/srun"

# Add to PATH
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ]; then
  if ! grep -q "gpu-scheduler" "$SHELL_RC" 2>/dev/null; then
    echo '' >> "$SHELL_RC"
    echo '# local-gpu-scheduler' >> "$SHELL_RC"
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
    echo "✅ Added to PATH in $SHELL_RC"
  else
    echo "✅ PATH already configured"
  fi
fi

export PATH="$INSTALL_DIR:$PATH"

echo ""
echo "✅ Installed! Run these commands to get started:"
echo ""
echo "   source $SHELL_RC          # reload PATH (or open a new terminal)"
echo "   python $INSTALL_DIR/run_server.py --detach   # start scheduler"
echo "   srun python your_script.py                   # run a GPU job"
echo ""
