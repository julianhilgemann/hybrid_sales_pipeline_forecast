#!/usr/bin/env bash
# Render one clip.
#
#   ./render.sh <clip-id> <quality> [extra manim args]
#
#   clip-id : s01 .. s07   (scene file scenes/<clip-id>_*.py, scene class "Clip")
#   quality : draft   480p15   fast iteration
#             preview 720p30   review copy
#             final   1080p60  delivery
#             still   1080p    last frame only (PNG)
#
# Each clip renders into its own media dir (media/<clip-id>/) so parallel
# renders never collide. The finished video is copied to out/<quality>/.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/Library/TeX/texbin:$PATH"

clip="${1:?clip id, e.g. s03}"
quality="${2:-draft}"
shift $(( $# < 2 ? $# : 2 ))

file=$(ls scenes/"${clip}"_*.py 2>/dev/null | head -1)
[ -n "$file" ] || { echo "no scene file scenes/${clip}_*.py" >&2; exit 1; }
name=$(basename "$file" .py)

case "$quality" in
  draft)   flags=(-ql) ;;
  preview) flags=(-qm) ;;
  final)   flags=(-qh) ;;
  still)   flags=(-qh -s) ;;
  *) echo "unknown quality: $quality" >&2; exit 1 ;;
esac

.venv/bin/manim render "${flags[@]}" --media_dir "media/${clip}" --disable_caching \
  -o "${name}" "$@" "$file" Clip

mkdir -p "out/${quality}"
if [ "$quality" = "still" ]; then
  src=$(find "media/${clip}/images" -name "${name}*.png" | head -1)
  cp "$src" "out/still/${name}.png" && echo "-> out/still/${name}.png"
else
  src=$(find "media/${clip}/videos" -name "${name}.mp4" -newer "$file" -o -name "${name}.mp4" | xargs ls -t | head -1)
  cp "$src" "out/${quality}/${name}.mp4" && echo "-> out/${quality}/${name}.mp4"
fi
