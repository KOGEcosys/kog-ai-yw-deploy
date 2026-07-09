#!/usr/bin/env bash
set -euo pipefail

if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -version | head -1
  exit 0
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ffmpeg
elif command -v brew >/dev/null 2>&1; then
  brew install ffmpeg
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y ffmpeg
elif command -v yum >/dev/null 2>&1; then
  sudo yum install -y ffmpeg
elif command -v apk >/dev/null 2>&1; then
  sudo apk add ffmpeg
else
  echo "No supported package manager found. Install ffmpeg manually, then ensure ffmpeg is in PATH." >&2
  exit 127
fi

ffmpeg -version | head -1
