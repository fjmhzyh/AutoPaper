#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found"
  exit 1
fi

if ! command -v hdiutil >/dev/null 2>&1; then
  echo "hdiutil not found (macOS only)"
  exit 1
fi

if ! command -v pyinstaller >/dev/null 2>&1; then
  echo "pyinstaller not found. Install: pip install pyinstaller"
  exit 1
fi

VERSION="$(python3 scripts/make_release.py version)"
RELEASE_DIR="$(python3 scripts/make_release.py prepare --platform mac)"
APP_NAME="AutoPaper"
APP_PATH="$ROOT_DIR/dist/${APP_NAME}.app"
WORKER_PATH="$APP_PATH/Contents/MacOS/AutoPaperWorker"
CONFIG_PATH="$APP_PATH/Contents/Resources/config"
PHOTOS_PATH="$APP_PATH/Contents/Resources/photos"
DMG_NAME="${APP_NAME}-${VERSION}-mac.dmg"
DMG_PATH="$RELEASE_DIR/$DMG_NAME"
STAGE_DIR="$ROOT_DIR/build/dmg_stage"

python3 scripts/make_release.py clean-build
rm -rf "$STAGE_DIR"

echo "[mac] building app via PyInstaller..."
pyinstaller --noconfirm --clean build/autopaper.spec

if [[ ! -d "$APP_PATH" ]]; then
  echo "[mac] build failed: app bundle not found at $APP_PATH"
  exit 1
fi
if [[ ! -f "$WORKER_PATH" ]]; then
  echo "[mac] build failed: worker not found at $WORKER_PATH"
  exit 1
fi
if [[ ! -d "$CONFIG_PATH" ]]; then
  echo "[mac] build failed: config folder missing at $CONFIG_PATH"
  exit 1
fi
if [[ ! -d "$PHOTOS_PATH" ]]; then
  echo "[mac] build failed: photos folder missing at $PHOTOS_PATH"
  exit 1
fi

mkdir -p "$STAGE_DIR"
cp -R "$APP_PATH" "$STAGE_DIR/"
ln -s /Applications "$STAGE_DIR/Applications"

echo "[mac] creating dmg..."
hdiutil create \
  -volname "$APP_NAME" \
  -srcfolder "$STAGE_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "[mac] removing quarantine xattr from artifacts..."
xattr -dr com.apple.quarantine "$STAGE_DIR/${APP_NAME}.app" || true
xattr -dr com.apple.quarantine "$DMG_PATH" || true

echo "[mac] done"
echo "APP: $STAGE_DIR/${APP_NAME}.app"
echo "Worker: $WORKER_PATH"
echo "DMG: $DMG_PATH"
