#!/usr/bin/env bash
# Render every chapter and join them into the full film.
#
#   ./make_film.sh [quality] [parallel-jobs]
#
#   quality : draft | preview | final   (default: final = 1080p60)
#   jobs    : how many chapters to render at once (default: 4)
#
# Output: out/<quality>/sNN_*.mp4  and  out/film_<quality>.mp4
set -euo pipefail
cd "$(dirname "$0")"

quality="${1:-final}"
jobs="${2:-4}"
mkdir -p "out/${quality}" out/logs

clips=$(ls scenes/s[0-9][0-9]_*.py | sed -E 's#scenes/(s[0-9]{2})_.*#\1#' | sort -u)
echo "rendering: $(echo $clips | tr '\n' ' ') at ${quality}, ${jobs} at a time"

# shellcheck disable=SC2086
printf '%s\n' $clips | xargs -P "$jobs" -I{} sh -c \
  './render.sh {} '"$quality"' > out/logs/{}_'"$quality"'.log 2>&1 && echo "  done {}" || { echo "  FAILED {} (see out/logs/{}_'"$quality"'.log)"; exit 1; }'

film="out/film_${quality}.mp4"
.venv/bin/python tools/concat.py "out/${quality}" -o "$film"
.venv/bin/python tools/verify_film.py "out/${quality}" "$film" -o "review/film_sheet_${quality}.png"
