# Environment

The toolkit needs four things:

- a Python 3.11+ virtual environment with Manim Community (Cairo renderer)
- the system **cairo** library, because `pycairo` ships no macOS wheels and compiles against it
- **LaTeX** with `dvisvgm`, because all film text is `Tex` / `MathTex`
- `imageio-ffmpeg`, which supplies the ffmpeg binary the tools use for frame grabs and concatenation

A system ffmpeg is unnecessary: manim encodes through PyAV.

Verified on macOS 13.5 (Apple M1) with Homebrew, uv, Python 3.12, TeX Live 2022 and Manim 0.22.1. The Debian/Ubuntu package names in `setup.sh` are the standard ones and were not run.

## Symptoms and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `pycairo` build fails: `Dependency "cairo" not found` | no system cairo | `brew install cairo pkg-config`, then re-run `setup.sh` |
| `brew install cairo` runs `./configure` for many minutes | Homebrew has no bottles for this macOS release, so it compiles gettext, glib, the X11 libraries, pixman and cairo from source (about 45 minutes on an M1) | run it as a background command and work on the concept and the bundle meanwhile |
| `av` build fails: `Package 'libswscale' not found` | PyAV 16+ ships macOS 14+ wheels only; without a wheel it compiles against ffmpeg headers | pin `av==15.1.0` (`setup.sh` does this on macOS below 14) |
| `ffmpeg: command not found` | none installed system-wide | nothing to install; the tools call `imageio_ffmpeg.get_ffmpeg_exe()` |
| `latex` not found during a render | TeX is not on `PATH` | `render.sh` prepends `/Library/TeX/texbin`; elsewhere export the TeX bin directory |
| words render in Computer Modern instead of Source Sans Pro | `sourcesanspro.sty` is not installed; `common.py` falls back silently | `tlmgr install sourcesanspro` (MacTeX ships it); `setup.sh` reports the text font |
| a download of a prebuilt environment manager (`curl … \| tar`, micromamba) is denied | the permission classifier blocks fetching and running binaries | install through the system package manager and uv/pip |
| `ModuleNotFoundError` for the project's packages in a scene, or for `manim` in `build_data.py` | two interpreters by design | `build_data.py` runs with the project's interpreter, everything else with `FILM/.venv` |

## Budgets

Measured on an M1 (8 cores), Cairo renderer:

- The toolkit's 44 s smoke clip (2D, then about 600 tower faces) renders in 40 s at `draft` (480p15) and 110 s at `final` (1080p60).
- An eleven-chapter, 14.5-minute film: about 22 minutes of `final` renders in all; the densest 3D chapter (1:32, about 1000 tower faces, redrawn every frame by `setup_3d`'s host) took about 5 of them. `make_film.sh` runs four at a time.
- Disk: 370 MB for the venv, about 520 MB of media and output for a 15-minute film plus its first edition.
- A fresh `setup.sh` takes about 25 s once cairo and LaTeX are present.
