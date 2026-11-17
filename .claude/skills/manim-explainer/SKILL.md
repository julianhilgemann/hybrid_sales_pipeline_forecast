---
name: manim-explainer
description: Manim explainer film. Turns a model, algorithm, chart or idea in the repo into a 3Blue1Brown-style animated video driven by the project's real data. Use when asked to visualize, animate or explain something with manim, or to make an explainer clip or film.
---

# Manim explainer film

Produce a silent 3Blue1Brown-style **film** of the idea the user pointed at: 5–8 **chapters**, each one manim scene rendered to its own clip, joined into one movie. You are the **coordinator**: you own the concept, the data, the shared visual language and the review. Each chapter has one **author** (a parallel subagent, or you) who owns one scene file.

One loop runs at every level: render, make a **contact sheet**, look at it, fix. Nothing is approved unseen.

`TOOLKIT` is this skill's `toolkit/` folder. `FILM` is the working directory you create, `animation/` at the repo root unless the user names another.

## 1. Preflight: first, and in the background

```bash
mkdir -p FILM && cp -R TOOLKIT/. FILM/ && mv FILM/gitignore FILM/.gitignore && FILM/setup.sh
```

`setup.sh` prints one line per requirement. A `[MISSING]` native library can take 30–60 minutes to install: launch that install as a background command and carry on with steps 2 and 3 while it runs. On `[MISSING]` or `[FAILED]`, read [references/environment.md](references/environment.md).

Done when `setup.sh` exits 0.

## 2. Concept: write the spec

Read what the user pointed at: the figure or document (open images with Read) and the code that computes it. Where prose and code disagree, the code is the model; tell the user about the difference. Then fix the **spec**:

- **Claim**: the one sentence the film proves.
- **Notation**: every symbol with its definition taken from the code, one LaTeX spelling each.
- **Colour semantics**: one hue per concept, six at most.
- **Motif**: the recurring picture that shows the mechanism underneath the smooth charts (individual particles for a stochastic system, single records for an aggregate, one step for an iteration).
- **Chapters**: 5–8, each 35–55 s and one idea, in teaching order. The last reassembles the source figure and ends on the one-line formula. Per chapter: what the viewer must understand, the object it inherits, the object it hands on, 2D or 3D, and its **payoff** beat.

Tell the user the chapter list in one short message and continue.

Done when every panel of the source figure and every term of the final formula belongs to exactly one chapter, and every symbol has one spelling and one colour.

## 3. Bundle: real numbers in one file

Write `FILM/build_data.py`. It runs the project's real code in the configuration of the source figure and writes `FILM/data/bundle.json` with every number any chapter draws: inputs, intermediates, outputs, and whatever the motif needs (simulated realisations, individual records). It asserts the identities the film will show, such as marginals summing to totals and a simulation mean matching the model output. Run it with the project's interpreter; `FILM/.venv` holds only manim.

Done when it runs clean with its asserts, and you can name the bundle field behind every chart of every chapter.

## 4. Visual language: smoke test before fan-out

In `FILM/common.py`, fill the `>>> PROJECT` block with one alias per concept. Render `./render.sh s00 draft`, then `./render.sh s00 final`; make a contact sheet with `tools/contact_sheet.py` and Read it. Note both render times for the guide, then delete `scenes/s00_smoke.py`.

Done when the smoke clip renders at `final` and its text is crisp in a full-resolution still.

## 5. Briefs

Read [references/manim-pitfalls.md](references/manim-pitfalls.md). Fill [references/agent-guide.md](references/agent-guide.md) with the spec, the bundle schema and the render times, and save it as `FILM/GUIDE.md`: the single binding document every author reads first. Write one **chapter brief** per chapter from [references/chapter-brief.md](references/chapter-brief.md).

Done when each brief states what the viewer must understand, lists its beats in order, names its payoff beat, its hand-offs to both neighbours and its things-to-get-right.

## 6. Fan out

Spawn one author per chapter, all in a single message so they run in parallel. Each prompt is "read `FILM/GUIDE.md`" plus that chapter's brief. Authors iterate at `draft`, deliver a `preview`, and leave `final` to you. Use the model the user names, otherwise the session default. Without subagents, write the chapters yourself in order with the same loop.

Measured on a seven-chapter film with the strongest model: a 2D chapter took 7–13 minutes and 125–165k tokens, a 3D chapter 17–25 minutes and 175–285k tokens, about 1.25M tokens in total.

Done when every chapter has an author at work.

## 7. Review: every clip, with your own eyes

As each author reports, make one contact sheet of its preview and pull full-resolution stills at its payoff beat and its densest frame. Judge them against [references/review.md](references/review.md). Approve, or send one revision message to the same author: resuming it keeps its context, so a revision costs minutes where a fresh author costs the chapter again.

- Show each approved preview to the user the moment it passes. Copy it first; authors overwrite their previews.
- Render approved chapters at `final` in the background, three at a time, while the rest are in revision.

Done when every chapter is approved from frames you looked at and every `final` clip exists.

## 8. Assemble and verify

```bash
.venv/bin/python tools/concat.py out/final -o out/<name>.mp4
.venv/bin/python tools/verify_film.py out/final out/<name>.mp4 -o review/film_sheet.png
```

Read the sheet and two 1080p stills: the densest 3D frame and the last frame.

Done when `verify_film.py` prints `VERIFIED`, the sheet shows the chapters in order and the stills are crisp. Open the film for the user and report its location and length, what you sent back and why, and every compromise: numbers that differ from the source figure, anything simulated rather than produced by the model, anything left out.
