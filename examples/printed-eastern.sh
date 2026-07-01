#!/usr/bin/env bash
set -euo pipefail

input=${1:-page.png}
output=${2:-page.txt}

kraken \
  -i "$input" "$output" \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEastSyr_01_18.mlmodel --base-dir R
