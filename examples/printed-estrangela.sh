#!/usr/bin/env bash
set -euo pipefail

input=${1:-page.png}
output=${2:-page.txt}

kraken \
  -i "$input" "$output" \
  segment -bl -i syr_print_seg03_91.mlmodel -d horizontal-rl \
  ocr -m SyrEstr_02_34.mlmodel --base-dir R
