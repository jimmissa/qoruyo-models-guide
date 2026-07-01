#!/usr/bin/env bash
set -euo pipefail

models=(
  "10.5281/zenodo.17406626"
  "10.5281/zenodo.17406677"
  "10.5281/zenodo.17406703"
  "10.5281/zenodo.17406690"
  "10.5281/zenodo.17406717"
  "10.5281/zenodo.17406754"
  "10.5281/zenodo.17406766"
  "10.5281/zenodo.17406773"
)

for model in "${models[@]}"; do
  printf 'Downloading %s\n' "$model"
  kraken get "$model"
done

printf 'All model retrieval commands completed.\n'
