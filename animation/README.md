# Animated explainer

A silent, 3Blue1Brown-style film of the forecasting model: how a stream of opportunities becomes a forecast of wins. Seven chapters, 5 min 52 s, 1080p60, built with [Manim Community](https://www.manim.community/) from the model's real output (as-of 2025-05-01, 15 business-day horizon, max age 45).

| # | Chapter | Scene | Length |
|---|---|---|---|
| 01 | The stream of opportunities | [s01_stream.py](scenes/s01_stream.py) | 0:49 |
| 02 | The decision kernel | [s02_kernel.py](scenes/s02_kernel.py) | 0:55 |
| 03 | Wins from the existing pipeline (3D) | [s03_stock.py](scenes/s03_stock.py) | 0:59 |
| 04 | Forecasting arrivals | [s04_arrivals.py](scenes/s04_arrivals.py) | 0:35 |
| 05 | Wins from future arrivals (3D) | [s05_convolution.py](scenes/s05_convolution.py) | 0:55 |
| 06 | The forecast (2D to 3D) | [s06_forecast.py](scenes/s06_forecast.py) | 0:55 |
| 07 | The whole machine | [s07_machine.py](scenes/s07_machine.py) | 0:44 |

Rendered video is not committed; build it locally.

## Build

```bash
cd animation
./setup.sh                          # manim environment in ./.venv (needs cairo and LaTeX)
./make_film.sh                      # every chapter at 1080p60, joined and verified -> out/
./render.sh s03 preview             # one chapter at 720p30 (draft | preview | final | still)
../.venv/bin/python build_data.py   # optional: regenerate data/model_data.json from the pipeline
```

`build_data.py` runs with the project's interpreter (it needs duckdb and pandas); everything else runs with `animation/.venv`.

| File | Role |
|---|---|
| [build_data.py](build_data.py) | runs the real pipeline and writes the one data file every scene reads, including 400 simulated futures of the same system |
| [common.py](common.py) | shared palette, type scale, chapter open/close, chart and 3D builders |
| [render.sh](render.sh), [make_film.sh](make_film.sh) | render one chapter; render all and join |
| [tools/](tools/) | contact sheets and stills from a clip, lossless concat, film verification |

## How it was made

One coordinating Claude session prepared the ground, seven parallel Opus subagents each built one chapter, and the coordinator reviewed every clip frame by frame before it was accepted.

### 1. Concept

The source was the README's main chart and the code behind it ([modeling.py](../pipeline_lib/modeling.py)). From those came a fixed specification:

- **Claim.** The forecast is the expectation of a stochastic system: opportunities arrive, age, and convert according to a kernel.
- **Notation.** `k(a)`, `S(a)`, `h_w(a)`, `N(a)`, `Â(t)`, `W_stock(d)`, `W_arr(d)`, `Ŵ(d)`, each defined from the code, with forecast days numbered from 1 so the formulas stay clean.
- **Colour semantics.** Amber for the kernel and a win, rose for existing stock, blue for arrivals, teal for the forecast, lavender for survival, slate for a loss.
- **Motif.** One opportunity is always a small dot. The smooth charts are what the dots do on average.
- **Chapters.** Seven, one idea each, ending by reassembling the README chart.

### 2. Environment

Getting manim to run took about 55 minutes, almost all of it one compile:

| Pitfall | What happened | Resolution |
|---|---|---|
| no cairo | `pycairo` has no macOS wheels and failed to build | `brew install cairo` |
| no Homebrew bottles for macOS 13 | brew compiled about 15 formulas from source, roughly 45 minutes | let it run in the background and prepared data, style and briefs meanwhile |
| PyAV wheels need macOS 14 | `av` 19 failed to build without ffmpeg headers | pinned `av==15.1.0` |
| no ffmpeg | none installed | not needed: manim encodes through PyAV, the tools use the `imageio-ffmpeg` binary |
| quick fix blocked | downloading micromamba with `curl \| tar` was denied by the permission classifier | stayed with Homebrew and uv |

### 3. Data bundle

[build_data.py](build_data.py) runs the real pipeline in the README chart's configuration and writes [data/model_data.json](data/model_data.json): kernel, hazards, survival, stock by age, both surfaces, the forecast, real opportunity lifelines, and a Monte Carlo of the same system. Asserts confirm that each surface sums to its daily totals. The simulated mean (49.35 wins over the horizon) matches the model (49.71).

Regenerating as-of 2025-05-01 with today's code gives slightly different numbers than the committed README image, which came from an earlier simulation setup. The film follows the code.

### 4. Shared visual language

[common.py](common.py) was written and smoke-tested before any chapter existed: a 14-second 3D clip rendered in 12 s at draft and 70 s at 1080p60, which set the render budgets for the authors.

### 5. Briefs

One shared guide (notation, colours, data schema, house style, technical rules, the render-and-look loop, report format) and one storyboard per chapter: what the viewer must understand, the beats in order, the hand-offs to neighbouring chapters, and the things to get right.

### 6. Fan-out

Seven authors ran in parallel, each owning one scene file and one media directory. Each iterated at 480p15, looked at its own contact sheets and stills, and delivered a 720p30 preview.

| Chapter | First version | Tokens | Sent back for |
|---|---|---|---|
| 04 arrivals | 7 min | 135k | nothing |
| 01 stream | 10 min | 127k | nothing |
| 06 forecast | 11 min | 210k | 3D fan of futures read as a wireframe skyline; bars filled a third of their axis |
| 07 machine | 13 min | 158k | large blocks swept across the arrivals heat-map during the pour |
| 02 kernel | 13 min | 160k | nothing |
| 05 convolution (3D) | 17 min | 177k | nothing |
| 03 stock (3D) | 25 min | 284k | collapse too fast; striped band-to-bar hand-off; overlapping captions |

About 1.25M subagent tokens in total. Each revision took three to four minutes because the same author was resumed with its context intact.

### 7. Review and assembly

Every preview was judged from one contact sheet and two or three full-resolution stills. Approved chapters were rendered at 1080p60 three at a time (43–187 s each) while the last ones were still in revision, then joined by stream copy. The film was checked for identical stream parameters, total duration, a clean fade to background at every chapter join, chapter order, and crisp 1080p frames.

From launching the authors to the finished film: 32 minutes.

## What made it efficient, and what to do next time

- **Start slow installs first and in the background.** The only real delay was waiting on a compile.
- **Fix the specification before fan-out.** Binding notation, colour semantics and a real-data bundle are what let seven independent authors produce one film.
- **Smoke-test the shared helpers yourself.** Authors then spend their effort on the chapter.
- **Give authors eyes.** The contact-sheet tool lets an author see its own clip; most defects never reached review.
- **Review cheaply.** One sheet plus stills at the payoff beat and the densest frame.
- **Resume, don't respawn.** A targeted, timestamped revision to the same author costs minutes.
- **Render finals as chapters are approved**, not after the last one.
- **Put the recurring defects into the rules up front.** Sequential caption swaps, a 2.5–3 s payoff beat, data that fills its axes, thin depth-graded lines for dense 3D, collapsing copies instead of originals. Five of the six revision requests were instances of these.

The reusable version of this process is the `manim-explainer` skill in [.claude/skills/manim-explainer/](../.claude/skills/manim-explainer/): the eight-step recipe, a portable toolkit with these fixes built into its shared helpers, and references for the environment, manim pitfalls, author guide, chapter briefs and review. Copy that folder into another repository's `.claude/skills/` and ask Claude to visualize an idea with manim.

## Known compromises

- Chapter 06 draws 40 of the 400 simulated futures; the 14 runs that exceed 9 wins on some day are left out of the picture but counted in the band and the mean.
- The spread band in chapter 06 is a simulation of the system, labelled "simulated spread". The model itself outputs the expectation.
- The 3D relief in chapter 03 is dense at ages 0–15 because ribbon heights follow the real, uneven stock counts.
