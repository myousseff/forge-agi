#!/usr/bin/env bash
set -euo pipefail
OUT="${1:-project_code_only.zip}"
echo "Creating slim zip -> $OUT"
zip -r "$OUT" .   -x "*.git/*" ".git/*" ".git"   -x "node_modules/*" "node_modules/**"   -x "build/*" "build/**"   -x ".dart_tool/*" ".dart_tool/**"   -x ".gradle/*" ".gradle/**"   -x "android/.gradle/*" "android/.gradle/**"   -x "android/gradle/*" "android/gradle/**"   -x ".venv/*" ".venv/**"   -x "dist/*" "dist/**"   -x "*.apk" "*.aab" "*.ipa" "*.xcarchive"   -x "*.keystore" "*.jks"   -x "ios/Pods/*" "ios/Pods/**"   -x "ios/.symlinks/*" "ios/.symlinks/**"
echo "Done."
