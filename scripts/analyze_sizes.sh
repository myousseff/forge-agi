#!/usr/bin/env bash
set -euo pipefail
echo "Top-level size (du -h -d1):"
du -h -d1 . | sort -hr | head -n 30

echo
echo "Largest 30 files:"
find . -type f -printf '%s %p\n' | sort -nr | head -n 30 | awk '{printf("%s\t%s\n",$1,$2)}'
