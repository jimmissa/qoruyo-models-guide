#!/usr/bin/env bash
set -euo pipefail

input=${1:-page.png}
output=${2:-page.txt}

kraken \
  -i "$input" "$output" \
  segment -bl -i syr_4col_99_segmonto.mlmodel -d horizontal-rl \
  ocr -m syr_41transcribathon_docs_d_3.mlmodel --base-dir R
