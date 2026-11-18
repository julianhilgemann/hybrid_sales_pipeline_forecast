---
name: manim-explainer
description: Manim explainer film. Turns a model, algorithm, chart or idea in the repo into a 3Blue1Brown-style animated video driven by the project's real data. Use when asked to visualize, animate or explain something with manim, or to make, extend or polish an explainer clip or film.
---

# Manim explainer film

Produce a silent 3Blue1Brown-style **film** of the idea the user pointed at: 8–12 **chapters**, each one manim scene rendered to its own clip, joined into one movie. You are the **coordinator**: you own the concept, the data, the shared visual language and the review. Each chapter has one **author** (a parallel subagent, or you) who owns one scene file.

The film is made for the **newcomer**: someone who has never seen the idea and is not a mathematician, yet should leave with the real formulas. A film that is correct but dense fails them; a first edition at 35–55 s per chapter was judged "full force, way too fast, hard to follow". Pace, definitions and tangents are the product, not padding.

One loop runs at every level: render, make a **contact sheet**, look at it, fix. Nothing is approved unseen.

`TOOLKIT` is this skill's `toolkit/` folder. `FILM` is the working directory you create, `animation/` at the repo root unless the user names another.

## 1. Preflight: first, and in the background

```bash
mkdir -p FILM && cp -R TOOLKIT/. FILM/ && mv FILM/gitignore FILM/.gitignore && FILM/setup.sh
```

`setup.sh` prints one line per requirement. A `[MISSING]` native library can take 30–60 minutes to install: launch that install as a background command and carry on with steps 2 and 3 while it runs. On `[MISSING]` or `[FAILED]`, read [references/environment.md](references/environment.md).

When FILM already holds a film the user wants extended or polished, skip the copy: diff its `common.py` against the toolkit's and bring over what it lacks, keep the old scenes in git and the old film in `out/v1/`, and make a contact sheet of the old film to list every place a newcomer gets lost.

Done when `setup.sh` exits 0.

## 2. Concept: write the spec

Read what the user pointed at: the figure or document (open images with Read) and the code that computes it. Where prose and code disagree, the code is the model; tell the user about the difference. Then fix the **spec**:

- **Claim**: the one sentence the film proves.
- **Notation**: every symbol with its definition taken from the code, one LaTeX spelling each, and the plain words that introduce it on screen.
- **Colour semantics**: one hue per concept, six at most.
- **Motif**: the recurring picture that shows the mechanism underneath the smooth charts (individual particles for a stochastic system, single records for an aggregate, one step for an iteration). A small population of the motif (a cohort of 100) is the best device for probability ideas.
- **Parts and chapters**: 8–12 chapters of 55–95 s, grouped into 3–5 parts with a label each, in teaching order:
  - the **basics** first: what one record is, the outcomes it can have, the clock it runs on, each defined on a card before any chart;
  - a **tangent** chapter for each idea the formula rests on (a hazard as a conditional probability, survival as a chain of daily chances), worked on the motif population before the formula appears;
  - the last chapter reassembles the source figure and ends on the one-line formula.

  Per chapter: its **guiding question** (on the opening card), its **takeaway** (the one-line answer at the end), what the viewer must understand, the object it inherits, the object it hands on, 2D or 3D, and its **payoff** beat.

Tell the user the chapter list in one short message and continue.

Done when every panel of the source figure and every term of the final formula belongs to exactly one chapter, every symbol has one spelling, one colour and its words, and every chapter's takeaway answers its question.

## 3. Bundle: real numbers in one file

Write `FILM/build_data.py`. It runs the project's real code in the configuration of the source figure and writes `FILM/data/bundle.json` with every number any chapter draws: inputs, intermediates, outputs, and whatever the motif and the tangents need (simulated realisations, a sample of real records, a motif population whose counts are rounded expectations of the real rates, the worked example of one row or one cell). It asserts the identities the film will show: marginals summing to totals, a simulation mean matching the model output, the worked example equal to the model's own row, the motif population tracking the model within rounding. Run it with the project's interpreter; `FILM/.venv` holds only manim.

An assert that fails, or a value that surprises you, can be a doubt about the model itself. The film follows the code; carry the doubt to the final report with its size in the model's numbers.

Done when it runs clean with its asserts, and you can name the bundle field behind every chart of every chapter.

## 4. Visual language: smoke test before fan-out

In `FILM/common.py`, fill the `>>> PROJECT` block: one alias per concept, one heat ramp per surface, the part labels. Render `./render.sh s00 draft`, then `./render.sh s00 final`; make a contact sheet with `tools/contact_sheet.py` and Read it. Then point the film's 3D builder (usually `HeatTowers`) at the **real** bundle matrix and run its whole grammar once: rise, top view, collapse, merge. Real data shows defects synthetic data hides; the rim at the foot of stacked towers appeared only there. Note the render times for the guide, then delete `scenes/s00_smoke.py`.

Done when the smoke clip renders at `final`, its text is crisp in a full-resolution still, and the 3D grammar ran clean on the real matrix.

## 5. Briefs

Read [references/manim-pitfalls.md](references/manim-pitfalls.md). Fill [references/agent-guide.md](references/agent-guide.md) with the spec, the bundle schema and the render times, and save it as `FILM/GUIDE.md`: the single binding document every author reads first. Write one **chapter brief** per chapter from [references/chapter-brief.md](references/chapter-brief.md).

Done when each brief states its guiding question and takeaway, what the viewer must understand, its beats in order with their captions, its payoff beat, its hand-offs to both neighbours and its things-to-get-right.

## 6. Fan out

Spawn one author per chapter, all in a single message so they run in parallel. Each prompt is "read `FILM/GUIDE.md`" plus that chapter's brief. Authors iterate at `draft`, deliver a `preview`, and leave `final` to you. Use the model the user names, otherwise the session default. Without subagents, write the chapters yourself in order with the same loop.

Measured with the strongest model on an eleven-chapter film of 14.5 minutes: 15–62 minutes and 210–460k tokens per chapter, the 3D chapters at the top, about 3.4M tokens in total.

Done when every chapter has an author at work.

## 7. Review: every clip, with your own eyes

As each author reports, make one contact sheet of its preview and pull full-resolution stills at its payoff beat and its densest frame. Judge them against [references/review.md](references/review.md), first as the newcomer, then as a critic. Approve, or send one revision message to the same author: resuming it keeps its context, so a revision costs minutes where a fresh author costs the chapter again.

- Show each approved preview to the user the moment it passes. Copy it to `out/show/` first; authors overwrite their previews.
- Render approved chapters at `final` in the background, three at a time, while the rest are in revision.

Done when every chapter is approved from frames you looked at and every `final` clip exists.

## 8. Assemble and verify

```bash
.venv/bin/python tools/concat.py out/final -o out/<name>.mp4
.venv/bin/python tools/verify_film.py out/final out/<name>.mp4 -o review/film_sheet.png
```

Read the sheet and two 1080p stills: the densest 3D frame and the last frame.

Done when `verify_film.py` prints `VERIFIED`, the sheet shows the chapters in order and the stills are crisp. Open the film for the user and report its location and length, what you sent back and why, every compromise (numbers that differ from the source figure, anything simulated rather than produced by the model, anything left out, any illustration that is not data), and every doubt about the model from step 3.

## 9. Fold back

Every author reports the gaps in the shared helpers and its workarounds. Collect them; the ones two chapters hit, or that cost an author real time, go into `TOOLKIT/common.py` (as a helper or a parameter, smoke-tested), the rest into [references/manim-pitfalls.md](references/manim-pitfalls.md). Change `FILM/common.py` only additively: every approved chapter was rendered with its current defaults, so re-render one that uses a changed helper and compare its frames with the approved preview.

Done when every reported gap is either in the toolkit, in the pitfalls, or named to the user as deliberately left out.
