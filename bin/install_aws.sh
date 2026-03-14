#!/usr/bin/bash
set -euo pipefail

ARCH="$(uname -m)"
TMP_DIR="$(mktemp -d)"
cd "$TMP_DIR"

if [ "$ARCH" = "x86_64" ]; then
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
elif [ "$ARCH" = "aarch64" ]; then
  curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
else
  echo "Unsupported architecture: $ARCH" >&2
  exit 1
fi

unzip awscliv2.zip
sudo ./aws/install

aws --version
