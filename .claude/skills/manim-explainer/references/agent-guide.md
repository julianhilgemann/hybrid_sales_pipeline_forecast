# Author guide template

Fill every `{{…}}` and save the result as `FILM/GUIDE.md`. Everything outside the braces applies to any film and stays as written.

---

# {{FILM TITLE}}: shared guide for chapter authors

## What we are making

A silent, 3Blue1Brown-style explainer film: charts, animation, LaTeX math and short on-screen text, with no narration or audio. It explains {{what, and the source figure or document it follows}}.

The film proves one claim: {{claim}}.

It has {{N}} chapters. Each is one manim scene rendered to its own clip; the clips are joined. **You own exactly one chapter.** The other authors are building theirs in parallel right now, so the conventions below are binding: the film must feel like one piece.

Working directory for everything: `{{absolute path of FILM}}`

Read first, in this order:

1. this guide
2. `{{source figure or document}}` (open images with Read)
3. `common.py`: palette, type scale, data loader, builders
4. `{{the code that implements the model}}`
5. `{{absolute path of the skill}}/references/manim-pitfalls.md`

## The model: notation is binding

{{The mechanism in plain language, then every quantity with its exact definition from the code. One line each: symbol, meaning, formula.}}

LaTeX spellings to use everywhere: {{list}}.

Colour semantics (aliases in `common.py`); colour the maths like the objects it denotes:

| thing | constant |
|---|---|
| {{concept}} | `{{ALIAS}}` |
| neutral text and marks | `INK`; secondary `MUTED`; grid `GRID` |

The motif: {{the recurring picture, e.g. "one opportunity is always a small dot; a win is an amber flash"}}. The smooth charts are what the motif does on average.

## Film outline

| # | chapter title (use verbatim) | accent | scene type | target length |
|---|---|---|---|---|
| 01 | {{title}} | `{{ALIAS}}` | {{2D / 3D}} | {{35–55 s}} |

Every clip starts from an empty background, calls `open_chapter(self, number, title, accent)` (chapter 01 calls `film_title` first), tells its story and ends with `close_chapter(self)`. Neighbouring chapters are made by other authors, so re-establish any object you inherit instead of assuming it is on screen.

## Data: animate the real numbers

`D = load_data()` returns the project's actual output for {{configuration}}. Read every value from `D`; the bars and curves are data, and only the motif may illustrate.

{{Bundle schema: each section, each field, its shape and meaning, and any trap such as a pooled bucket or a 1-based index.}}

## House style

- Dark background, a handful of saturated semantic colours, plenty of empty space.
- All text is LaTeX (`Tex` / `MathTex`) at the `FS_*` sizes from `common.py`; `FS_TICK` (22) is the floor.
- Things turn into other things: `Transform`, `ReplacementTransform`, `TransformFromCopy`, `TransformMatchingTex`. Formula terms fly out of the objects they denote.
- One new idea on screen at a time; build charts progressively.
- Motion is smooth and unhurried; camera moves take 2–4 s.
- Silent film means reading time: a caption stays at least 2.5 s with nothing else demanding attention, a new formula at least 3 s. Captions are nine words at most, sentence case, no full stop, in the standard bottom position, changed with `swap_caption`.
- The **payoff** beat of your chapter, the transform that carries its idea, runs 2.5–3 s and is followed by a hold.
- Data fills its axes: at least 60% of the plot height. Start tight and rescale when larger data arrives.
- The chapter header stays top-left for the whole clip; keep that corner clear. Keep 0.35 units of margin to the frame edge (the frame is 14.22 × 8).
- Axes are thin and muted, with a short title and a few tick numbers.
- Every mark serves the explanation.

## Technical rules

- Manim Community {{version}}, Cairo renderer. Python: `.venv/bin/python`, `.venv/bin/manim`.
- Your file is `scenes/sNN_<slug>.py` with one class named `Clip` (`Scene`, `MovingCameraScene` or `ThreeDScene`), starting with:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  from common import *
  ```
- Randomness uses `np.random.default_rng(<fixed seed>)`.
- You edit your own scene file and nothing else. For a gap in a shared helper, work around it inside your file and report it. Leave git and package installation to the coordinator.
- Render with `./render.sh sNN draft|preview|still`. Each clip has its own `media/sNN/`. Other renders are running: iterate at `draft`, one render at a time. `final` belongs to the coordinator.
- Measured here: {{draft and final render times of the smoke clip}}. A chapter whose `draft` takes over four minutes needs simplifying.
- 3D chapters: under about 900 polygons on screen; `ribbon_3d` and `floor_tiles_3d` are the building blocks; pin text with `fix_in_frame` before animating it; look at a mid-move frame of every camera move.

## Workflow and verification

1. Write the scene, then `./render.sh sNN draft`.
2. `.venv/bin/python tools/contact_sheet.py out/draft/<file>.mp4 --every 2 -o review/sNN_sheet.png`, then Read the PNG. `--start/--end` with a smaller `--every` zooms into a transition. Each tile carries its timestamp bottom-right.
3. Review every beat as a harsh critic, fix, re-render. Look for: overlapping or clipped text; anything touching the frame edge or the header; text below size 22; wrong colour semantics; a formula that departs from the notation; a number that departs from `D`; dead time; a beat too fast to read; a payoff that rushes; depth-sorting pops; objects left behind.
4. When the draft is right, `./render.sh sNN preview` and pull full-resolution stills at five or more key moments: `… tools/contact_sheet.py out/preview/<file>.mp4 --at 6,14.5,22 -o review/sNN_still.png`. Read them and fix what is not crisp. Complete at least two full review passes.
5. Leave `out/preview/sNN_*.mp4` in place.

## Report back

Plain text:

- scene file, preview video, duration, preview render time
- the beats in order, one line each with approximate timestamps
- the stills you checked and anything you are not fully happy with
- every gap in the shared helpers and your workaround
