# Coordinator review

## Looking at a clip

```bash
.venv/bin/python tools/contact_sheet.py out/preview/sNN_x.mp4 --every 2.5 --cols 4 --width 640 -o review/coord_sNN.png
.venv/bin/python tools/contact_sheet.py out/preview/sNN_x.mp4 --at <payoff>,<densest> -o review/coord_sNN_still.png
```

One sheet and two or three stills decide most clips. Zoom into a suspect transition with `--start/--end --every 0.4`.

## Checklist

Approve when all of these hold in the frames. Read the sheet twice: first as the newcomer, who has never seen the idea, then as a critic.

- The chapter opens on its guiding question and ends on a takeaway that answers it.
- Every symbol arrives with words the first time it appears; every caption holds at least 3 s; nothing reads as rushed.
- The motif tells the truth on every frame: each record shows its current state.
- The beats of the brief are present, in order, and each reads without the brief in hand.
- Colours match the semantics; every formula matches the notation; orientation matches the source figure.
- Text is crisp, at or above size 22, clear of the header, the frame edge and the data.
- Data fills its axes; the chart uses the frame.
- The payoff beat takes 2.5–3 s and is followed by a hold.
- 3D frames are clean: individual series can be followed, nothing pops in front mid-move.
- Captions never superimpose; nothing is left behind after a transition.
- The clip opens on the chapter card and ends on the bare background.

## Defects that recur

These were the revision requests on two films. Check for them first.

| Defect | Where | Request |
|---|---|---|
| the whole first edition: correct, but no definitions, symbols without words, 35–55 s chapters | every chapter | the newcomer rules of the guide: question card, definitions first, tangents on the motif population, 3 s captions, 55–95 s chapters |
| records that changed state keep their old colour (lost deals stayed "open" lavender), so a count on screen reads wrong | tangent chapter on the motif population | recolour each record on the beat its state changes; no extra time needed |
| 3D realisations drawn as translucent step curtains: a wireframe skyline | payoff chapter | thin straight-segment paths, depth-graded, 40–50 of them, spread further in depth |
| forecast bars fill a third of an axis sized for later data | payoff chapter | tight range first, animated rescale when the larger data arrives |
| large translucent blocks sweep across another panel during a "pour" | finale | copies collapse in place into chips the size of the result, then travel, staggered |
| the collapse onto the wall takes about a second | 3D construction | 4–5 s, staggered so the stack visibly builds |
| a bright rim at the foot of stacked towers | 3D construction | `merge` the stacks into solid bars |
| dashed stripes while stacked bands turn into bars | 3D construction | merge the bands into one area, bring the opaque bars in on top, then remove the area |
| two captions superimposed during a cross-fade | any | every swap sequential: old out, new in |

Accept and report, instead of sending back, what the data dictates: a relief that is dense because the real counts are uneven, near-empty series that stripe the far floor.

## Revision message

Send it to the same author. One message, with:

1. the verdict in the first line, and what is approved and must stay untouched
2. each change with its timestamp, what is wrong in the frame, and the concrete target
3. which changes are required and which are "only if it stays clean"
4. the length budget, and where to trim if a change adds time
5. what to re-check (a contact sheet of the changed span at a small `--every`, stills at named times) and how to report

## Showing and finishing

- Copy an approved preview before opening it (`out/show/`), since the author's next render overwrites `out/preview/`.
- Render approved chapters at `final` in the background while others are in revision.
- After the last approval: `concat.py`, `verify_film.py`, Read the film sheet and two 1080p stills.
