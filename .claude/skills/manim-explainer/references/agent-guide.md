# Author guide template

Fill every `{{…}}` and save the result as `FILM/GUIDE.md`. Everything outside the braces applies to any film and stays as written.

---

# {{FILM TITLE}}: shared guide for chapter authors

## What we are making

A silent, 3Blue1Brown-style explainer film: charts, animation, LaTeX math and short on-screen text, with no narration or audio. It explains {{what, and the source figure or document it follows}}.

The viewer **has never seen this and is not a mathematician**. They should come away understanding {{the three to five ideas a newcomer must leave with}}, while still seeing the real formulas.

The film proves one claim: {{claim}}.

It has {{N}} chapters in {{P}} parts, about {{minutes}} minutes. Each is one manim scene rendered to its own clip; the clips are joined. **You own exactly one chapter.** The other authors are building theirs in parallel right now, so the conventions below are binding: the film must feel like one piece.

Working directory for everything: `{{absolute path of FILM}}` (run every command from there). Your scratch files go in `{{scratchpad}}/sNN/`, never the scratchpad root, which the other authors share.

Read first, in this order:

1. this guide
2. `{{source figure or document}}` (open images with Read)
3. `common.py`: palette, type, data loader, teaching devices, chart and 3D builders
4. `{{the code that implements the model}}`
5. `{{absolute path of the skill}}/references/manim-pitfalls.md`

## Teaching rules

These are binding and are what the coordinator reviews first.

- **Ask, show, name.** Every chapter opens with `open_chapter(..., question=..., part=PART[n])` and ends with `takeaway(...)`, then `close_chapter(self)`. In between: show the thing concretely, then give it its name and symbol.
- **Concrete before general.** One record before many; one row before the surface; the motif population before the formula. Name the instance on screen ("14 deals aged 8").
- **Words before symbols.** The first time the film shows a symbol it comes with a plain-language label (a `Brace` with words, a `callout`, or a `definition_card`). Inherited symbols get a brief re-label; never assume the viewer remembers.
- **One new idea on screen at a time.** At most one moving focus; dim (opacity 0.25–0.35) what is not being talked about rather than adding more.
- **Reading time.** A caption stays at least 3 s, and nothing new appears during its first 1.5 s. A new formula is built term by term and held at least 4 s. A definition card stays at least 4 s. After the payoff beat, hold at least 2.5 s.
- **Breathing room.** Roughly half of every chapter is stillness or slow ambient motion. If a chapter feels busy, cut a beat rather than speed it up.
- **Captions** are at most 10 words, sentence case, no full stop, in the standard bottom position. `swap_caption` changes one between beats; `caption_swap` changes one inside a longer animation. Old out, then new in, always.
- **The motif keeps telling the truth.** A record changes colour on the beat its state changes, never later.
- **Numbers on screen** come from `D` and are rounded for reading. Say "expected" for model outputs, "simulated" for anything that is not the model's own output.

## Polish rules

- Things turn into other things: `Transform`, `ReplacementTransform`, `TransformFromCopy`, `TransformMatchingTex`, or moving the existing object to its new place. Never fade a chart out and fade a near-identical one in. Formula terms fly out of the objects they denote.
- Re-layout by moving and scaling what is already on screen, not by rebuilding.
- Timing: entrances 0.8–1.2 s, transforms 1.5–2.5 s, camera moves 3–4 s; nothing visible pops in under 0.5 s. Default rate function `smooth`; long slides `rate_functions.ease_in_out_sine`.
- Emphasis: a soft `SurroundingRectangle(corner_radius=0.1, stroke_width=2)` in the accent colour, or dimming the rest; `Indicate`/`Flash` sparingly.
- Bars grow from their baseline, curves are drawn with `Create`, axes with `Create` (0.8–1.2 s).
- Layout: keep inside x ∈ [−6.75, 6.75], y ∈ [−3.6, 3.6] (the frame is 14.22 × 8). The header owns the top-left corner for the whole clip; the caption band (y < −3.0) belongs to captions.
- Data fills its axes (at least 60% of the plot height). Start tight and animate a rescale when larger data arrives.
- Every chart has an axis title in words with its unit and a few tick numbers. Text is never below `FS_TICK` (22).
- In 3D, keep holds of 3 s or more alive with `drift(...)` or a slow ambient rotation; stop it before the next camera move.

## The model: notation is binding

{{The mechanism in plain words, with every term a newcomer needs (the record, its outcomes, its clock) defined in a sentence. Then every quantity with its exact definition from the code: a table of symbol, meaning, formula or bundle field.}}

LaTeX spellings to use everywhere (split into separate `MathTex` strings to colour terms): {{list}}. Words for the same things: {{the plain-language names, one per concept}}.

Facts you may quote (all from the bundle): {{the handful of headline numbers, rounded as they appear on screen}}.

## Colour semantics

Colour the maths like the objects it denotes (aliases in `common.py`):

| thing | constant |
|---|---|
| {{concept}} | `{{ALIAS}}` |
| neutral text and marks | `INK`; secondary `MUTED`; grid `GRID`; panels `PANEL` |

**The motif:** {{the recurring picture, e.g. "one opportunity is always a small dot: open lavender, won amber, lost slate"}}. {{The motif population and the chapters that use it.}} The smooth charts are what the motif does on average.

## Film outline

| # | chapter title (use verbatim) | part | accent | type | target |
|---|---|---|---|---|---|
| 01 | {{title}} | `PART[1]` | `{{ALIAS}}` | {{2D / 3D}} | {{55–95 s}} |

Targets may stretch by 15% if the pacing needs it; never compress a beat to hit a length.

Every clip starts from an empty background, calls `open_chapter(self, number, title, accent, question=..., part=PART[n])` (chapter 01 calls `film_title` first), tells its story, calls `takeaway(...)` and ends with `close_chapter(self)`. Neighbouring chapters are made by other authors, so re-establish any object you inherit with a short build (at most 3 s) instead of assuming it is on screen.

## Data: animate the real numbers

`D = load_data()` returns the project's actual output for {{configuration}} (regenerate with `{{command}}`; never edit the bundle). Read every value from `D`; the bars and curves are data, and only the motif may illustrate.

{{Bundle schema: each section, each field, its shape and meaning, and any trap such as a pooled bucket or a 1-based index.}}

## Tools in `common.py`

- Chapter and text: `open_chapter`, `takeaway`, `film_title`, `close_chapter`, `caption`, `swap_caption(scene, old, text, *also)`, `caption_swap(scene, old, text, run_time)` (returns `(new, anims)` to ride inside another play), `text_line(parts, colors=...)` (colour one word of a sentence), `PART[n]`.
- Teaching devices: `definition_card(term, lines, color, icon=, aside=)`, `callout`, `legend_item`, `dot_grid` (the motif population), `TexCounter` (a number that changes, in the text font), `hatched_rect` (a pooled bucket).
- 2D: `Chart` (explicit data-to-scene maps: bars centred on integers, rescaling, shared baselines; `with_range` for an animated rescale), `make_axes`, `tick_labels`, `bars`, `hbars`, `curve`, `area_under`, `heat_grid`, `ramp_color`, `shade`.
- 3D: `setup_3d(self)` (first line of a 3D `construct()`), `CAM_3D`, `CAM_TOP`, `CAM_FRONT`, `view`, `cam_to` (zoom dip, early frame centre), `drift`, `delayed`, `fix_in_frame`, `pin_label` / `move_pins` / `place_pin`, `slide`, `hide_during`, `pinned`, `FloorLine` / `floor_grid` / `FloorPoly`, `ribbon_3d`, `floor_tiles_3d`, and `HeatTowers`:

```python
setup_3d(self)                                          # host mobject, flat shading, FloorLine camera
T = HeatTowers(M, cell_w=0.42, cell_d=0.14, z_scale=4.7, ramp=RAMP, origin=(x0, y0, 0), gamma=0.6)
T.set_lift(0.0)
row0 = np.where(T.ii == 0)[0]
self.set_camera_orientation(**CAM_FRONT, zoom=1.4)      # level: one raised row is a 2D bar chart
self.play(T.lift(0, 1, ks=row0), run_time=1.5)
cam_to(self, view(62, -58, 0.8), 3.5, added_anims=[     # tilt while the other rows rise
    T.lift(0, 1, ks=np.where(T.ii > 0)[0], order=lambda T: T.ii, lag=0.5)])
self.play(T.tint(lambda t: None if t.i == 8 else BG, mix=0.75))   # light one row, dim the rest
cam_to(self, view(0, -90, 0.8), 3, added_anims=[T.lift(1, 0)])    # straight down: the heat-map
cam_to(self, view(62, -58, 0.75), 3, added_anims=[T.lift(0, ZW / ZS)])   # rise at the wall scale
self.play(T.collapse(axis="y", z_scale_wall=ZW), run_time=4.5)    # stack every column on the wall
B = T.merge(self, COLOR)                                # stacks -> solid bars
cam_to(self, view(90, -90, 1.2, (0, T.wall, 1.4)), 3)   # the wall faces us: the 2D bar chart
```

{{Facts about the film's own use of it: matrix orientation, row origin, scales, measured face counts.}}

## Technical rules

- Manim Community {{version}}, Cairo renderer. Python: `.venv/bin/python`, `.venv/bin/manim`. All text is `Tex`/`MathTex` ({{text font}} for words, Computer Modern for maths). `\textbf`, `\textit`, `$...$` work in `Tex`; `\text{...}` in `MathTex`.
- Your file is `scenes/sNN_<slug>.py` with one class named `Clip` (`Scene`, `MovingCameraScene` or `ThreeDScene`), starting with:
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
  from common import *
  ```
- Randomness uses `np.random.default_rng(<fixed seed>)`.
- You edit your own scene file and nothing else. For a gap in a shared helper, work around it inside your file and report it. Leave git and package installation to the coordinator.
- Render with `./render.sh sNN draft|preview|still`. Each clip has its own `media/sNN/`. The other authors render at the same time: iterate at `draft`, one render at a time. `final` belongs to the coordinator.
- Measured here (alone on the machine): {{draft and final render times of the smoke clip}}. A chapter whose `draft` takes over five minutes needs simplifying.
- 3D chapters: `setup_3d(self)` first; stay under about 1000 polygons on screen; pin text with `fix_in_frame` before animating it; leave `frame_center` alone until after `open_chapter`; look at a mid-move frame of every camera move.

## Workflow and verification

1. Write the scene, then `./render.sh sNN draft`.
2. `.venv/bin/python tools/contact_sheet.py out/draft/<file>.mp4 --every 2 -o review/sNN_sheet.png`, then Read the PNG. `--start/--end` with a smaller `--every` zooms into a transition. Each tile carries its timestamp bottom-right.
3. Review every beat as a harsh critic **and as the newcomer**: would someone who has never seen this follow it without the brief? Look for: a symbol shown without words; a beat too fast to read; two things moving for attention; a record whose colour lags its state; overlapping or clipped text; anything touching the frame edge or the header; text below size 22; wrong colour semantics; a formula that departs from the notation; a number that departs from `D`; dead time; a payoff that rushes; depth-sorting pops; objects left behind; a chart swapped by fade instead of transformed.
4. When the draft is right, `./render.sh sNN preview` and pull full-resolution stills at five or more key moments: `… tools/contact_sheet.py out/preview/<file>.mp4 --at 6,14.5,22 -o review/sNN_still.png`. Read them and fix what is not crisp. Complete at least two full review passes.
5. Leave `out/preview/sNN_*.mp4` in place.

## Report back

Plain text:

- scene file, preview video, duration, preview render time
- the beats in order, one line each with approximate timestamps
- the stills you checked and anything you are not fully happy with
- every gap in the shared helpers and your workaround
