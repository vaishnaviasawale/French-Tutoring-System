#!/usr/bin/env bash
# Record a 16 kHz mono clip. Ctrl+C to stop.
#   ./02-pronunciation/record.sh s03_good
#   ./02-pronunciation/record.sh s03_bad      # same sentence, deliberately mispronounced
set -euo pipefail
name="${1:?usage: record.sh <name>   e.g. s03_good}"
out="$(dirname "$0")/recordings/${name}.wav"
echo "Recording to $out — Ctrl+C to stop"
pw-record --rate 16000 --channels 1 --format s16 "$out" || true
echo "Saved $out"
