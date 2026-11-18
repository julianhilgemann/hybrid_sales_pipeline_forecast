#!/usr/bin/env bash
# Preflight + environment for the explainer toolkit. Idempotent: run it again
# after fixing whatever it reports.
#
#   ./setup.sh
#
# Creates ./.venv with Manim Community + imageio-ffmpeg and prints one line per
# requirement: [ok], [MISSING] with the remedy, or [FAILED] with the log tail.
# Exit code 0 means every chapter can be rendered here.
set -uo pipefail
cd "$(dirname "$0")"
export PATH="/Library/TeX/texbin:$PATH"

status=0
say() { printf '%-10s %s\n' "$1" "$2"; }

# --- LaTeX (all film text is Tex/MathTex) -----------------------------------
if command -v latex >/dev/null 2>&1 && command -v dvisvgm >/dev/null 2>&1; then
  say "[ok]" "latex + dvisvgm"
else
  say "[MISSING]" "latex/dvisvgm. Install a full TeX distribution (macOS: MacTeX; a minimal BasicTeX needs extra tlmgr packages, see Manim's installation docs) and re-run."
  status=1
fi
if command -v kpsewhich >/dev/null 2>&1 && [ -n "$(kpsewhich sourcesanspro.sty 2>/dev/null)" ]; then
  say "[ok]" "text font Source Sans Pro"
elif command -v latex >/dev/null 2>&1; then
  say "[note]" "sourcesanspro.sty not found: words fall back to Computer Modern ('tlmgr install sourcesanspro' to fix; optional)"
fi

# --- cairo (pycairo compiles against it; it has no macOS wheels) -------------
if pkg-config --exists cairo 2>/dev/null; then
  say "[ok]" "cairo $(pkg-config --modversion cairo)"
else
  say "[MISSING]" "cairo. macOS: 'brew install cairo pkg-config' (on a macOS release Homebrew no longer bottles this compiles ~15 formulas from source, 30-60 min: start it in the background NOW). Debian/Ubuntu: libcairo2-dev pkg-config."
  status=1
fi

# --- virtual environment ----------------------------------------------------
pins=()
if [ "$(uname)" = "Darwin" ]; then
  major=$(sw_vers -productVersion | cut -d. -f1)
  # PyAV >= 16 ships macOS 14+ wheels only; without a wheel it needs system ffmpeg libs to build.
  [ "$major" -lt 14 ] && pins+=("av==15.1.0")
fi

if [ ! -x .venv/bin/python ]; then
  if command -v uv >/dev/null 2>&1; then uv venv --python 3.12 .venv >/dev/null 2>&1
  else python3 -m venv .venv; fi
fi
if [ -x .venv/bin/python ]; then
  log=$(mktemp)
  if command -v uv >/dev/null 2>&1; then
    uv pip install --python .venv/bin/python -r requirements.txt ${pins[@]+"${pins[@]}"} >"$log" 2>&1
  else
    .venv/bin/python -m pip install -q -r requirements.txt ${pins[@]+"${pins[@]}"} >"$log" 2>&1
  fi
  if [ $? -eq 0 ] && .venv/bin/manim --version >/dev/null 2>&1; then
    say "[ok]" "$(.venv/bin/manim --version 2>/dev/null | grep -m1 Manim) in ./.venv ${pins[*]+(pinned ${pins[*]})}"
  else
    say "[FAILED]" "pip install (see references/environment.md). Log tail:"
    grep -vE "^\s*$" "$log" | tail -8 | sed 's/^/           /'
    status=1
  fi
  rm -f "$log"
else
  say "[FAILED]" "could not create ./.venv (need uv or python3 >= 3.11)"
  status=1
fi

[ $status -eq 0 ] && say "[ready]" "next: ./render.sh s00 draft  (smoke test)"
exit $status
