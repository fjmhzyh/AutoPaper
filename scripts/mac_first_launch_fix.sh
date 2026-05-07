#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/mac_first_launch_fix.sh /path/to/AutoPaper.app"
  exit 1
fi

APP_PATH="$1"
if [[ ! -d "$APP_PATH" ]]; then
  echo "App not found: $APP_PATH"
  exit 1
fi

xattr -dr com.apple.quarantine "$APP_PATH"
echo "Removed quarantine attribute from: $APP_PATH"
