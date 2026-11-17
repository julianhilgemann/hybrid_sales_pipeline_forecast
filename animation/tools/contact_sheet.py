#!/usr/bin/env python3
"""Look at a rendered clip without playing it.

Contact sheet (default): frames sampled every N seconds, tiled with timestamps.

    python tools/contact_sheet.py media/s03/videos/.../Clip.mp4 --every 1.5 -o review/s03_sheet.png

Full-resolution stills at specific times (for checking crispness / overlaps):

    python tools/contact_sheet.py Clip.mp4 --at 4.0,12.5,31 -o review/s03_still.png
    # -> review/s03_still_004.00.png, review/s03_still_012.50.png, ...

Then open the PNGs with the Read tool.
"""

from __future__ import annotations

import argparse
import math
import re
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def duration(path: Path) -> float:
    out = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", out)
    if not m:
        raise SystemExit(f"could not read duration of {path}")
    h, mnt, s = m.groups()
    return int(h) * 3600 + int(mnt) * 60 + float(s)


def grab(path: Path, t: float, out: Path, width: int | None) -> None:
    cmd = [FFMPEG, "-y", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1"]
    if width:
        cmd += ["-vf", f"scale={width}:-2"]
    cmd.append(str(out))
    subprocess.run(cmd, check=True)
    if not out.exists() and t > 0.25:  # asked for a time past the last frame
        grab(path, t - 0.25, out, width)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("video")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--every", type=float, default=2.0, help="seconds between sampled frames")
    p.add_argument("--at", default=None, help="comma separated times -> full-res stills")
    p.add_argument("--start", type=float, default=0.0, help="sheet start time (s)")
    p.add_argument("--end", type=float, default=None, help="sheet end time (s)")
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--width", type=int, default=480, help="tile width in px")
    args = p.parse_args()

    video = Path(args.video)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dur = duration(video)

    if args.at:
        for t in [float(v) for v in args.at.split(",")]:
            t = min(max(t, 0.0), max(dur - 0.1, 0.0))
            target = out.with_name(f"{out.stem}_{t:06.2f}{out.suffix}")
            grab(video, t, target, None)
            print(target)
        return 0

    start = max(0.0, args.start)
    end = min(dur - 0.1, args.end) if args.end is not None else dur - 0.1
    times = [start + i * args.every for i in range(int(math.floor((end - start) / args.every)) + 1)]
    if end - times[-1] > 0.4 * args.every:
        times.append(end)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 18)
    except OSError:
        font = ImageFont.load_default()

    tiles = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, t in enumerate(times):
            f = Path(tmp) / f"f{i:04d}.png"
            grab(video, t, f, args.width)
            im = Image.open(f).convert("RGB")
            draw = ImageDraw.Draw(im)
            # timestamp bottom-right, so it never hides the chapter header (top-left)
            draw.rectangle([im.width - 92, im.height - 26, im.width, im.height], fill=(0, 0, 0))
            draw.text((im.width - 86, im.height - 23), f"{t:6.2f}s", fill=(255, 255, 0), font=font)
            tiles.append(im)

    w, h = tiles[0].size
    cols = min(args.cols, len(tiles))
    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * w + (cols + 1) * 4, rows * h + (rows + 1) * 4), (60, 60, 60))
    for i, im in enumerate(tiles):
        sheet.paste(im, (4 + (i % cols) * (w + 4), 4 + (i // cols) * (h + 4)))
    sheet.save(out)
    print(f"{out}  ({len(tiles)} frames, clip {dur:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
