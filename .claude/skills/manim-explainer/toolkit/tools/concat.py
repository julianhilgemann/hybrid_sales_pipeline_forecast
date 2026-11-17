#!/usr/bin/env python3
"""Join the per-chapter clips into the full movie (lossless stream copy).

    python tools/concat.py out/final -o out/pipeline_forecast_explainer.mp4
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("clip_dir")
    p.add_argument("-o", "--out", required=True)
    args = p.parse_args()

    clips = sorted(Path(args.clip_dir).glob("s[0-9][0-9]_*.mp4"))
    if not clips:
        raise SystemExit(f"no clips in {args.clip_dir}")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        for c in clips:
            f.write(f"file '{c.resolve()}'\n")
        listing = f.name
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", listing, "-c", "copy", "-movflags", "+faststart", str(out)],
        check=True,
    )
    print(f"{out}  <- {len(clips)} clips: {', '.join(c.stem for c in clips)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
