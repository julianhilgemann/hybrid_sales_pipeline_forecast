#!/usr/bin/env python3
"""Verify the assembled film against its chapter clips.

    python tools/verify_film.py out/final out/film.mp4 -o review/film_sheet.png

Checks, and exits non-zero if any fails:
  1. every clip and the film share codec, resolution and frame rate
  2. film duration equals the sum of the clip durations
  3. at every chapter join the picture is the bare background (clean fade)
Also writes a whole-film contact sheet to look at.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
HERE = Path(__file__).resolve().parent


def probe(path: Path) -> tuple[float, str]:
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out).groups()
    video = re.search(r"Video: (\w+).*?, (\d+x\d+).*?, ([\d.]+) fps", out)
    return int(h) * 3600 + int(m) * 60 + float(s), " ".join(video.groups())


def background() -> np.ndarray:
    src = (HERE.parent / "common.py").read_text()
    hexcol = re.search(r'^BG = "#([0-9A-Fa-f]{6})"', src, re.M).group(1)
    return np.array([int(hexcol[i:i + 2], 16) for i in (0, 2, 4)], dtype=float)


def frame(path: Path, t: float, tmp: str) -> np.ndarray:
    target = Path(tmp) / "f.png"
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(path),
                    "-frames:v", "1", str(target)], check=True)
    return np.asarray(Image.open(target).convert("RGB"), dtype=float)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("clip_dir")
    p.add_argument("film")
    p.add_argument("-o", "--sheet", default=None, help="write a whole-film contact sheet here")
    args = p.parse_args()

    clips = sorted(Path(args.clip_dir).glob("s[0-9][0-9]_*.mp4"))
    film = Path(args.film)
    ok = True

    film_dur, film_fmt = probe(film)
    durations = []
    for c in clips:
        dur, fmt = probe(c)
        durations.append(dur)
        same = fmt == film_fmt
        ok &= same
        print(f"{'ok  ' if same else 'FAIL'} {c.name:32s} {dur:7.2f}s  {fmt}")
    total = sum(durations)
    same = abs(total - film_dur) < 0.1 * len(clips)
    ok &= same
    print(f"{'ok  ' if same else 'FAIL'} film {film_dur:.2f}s vs sum of clips {total:.2f}s  ({film_fmt})")

    bg = background()
    with tempfile.TemporaryDirectory() as tmp:
        for name, j in zip([c.stem for c in clips[1:]], np.cumsum(durations)[:-1]):
            # share of pixels that are visibly not background (a leftover header is ~0.3%)
            worst = max((np.abs(frame(film, j + dt, tmp) - bg).max(axis=2) > 16).mean() for dt in (-0.05, 0.05))
            clean = worst < 0.0005
            ok &= clean
            print(f"{'ok  ' if clean else 'FAIL'} join before {name:24s} at {j:7.2f}s  non-background pixels {worst:.3%}")

    if args.sheet:
        every = max(4.0, round(film_dur / 32))
        subprocess.run([sys.executable, str(HERE / "contact_sheet.py"), str(film), "--every", str(every),
                        "--cols", "6", "--width", "420", "-o", args.sheet], check=True)
    print("VERIFIED" if ok else "PROBLEMS FOUND")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
