# Chapter brief

One brief per chapter, sent as the author's prompt. The guide carries everything shared; the brief carries only what is particular to this chapter.

## Shape

```text
You are one of {{N}} authors building a silent, 3Blue1Brown-style manim explainer film about
{{subject}} for a viewer who has never seen it. You own **chapter NN: "{{title}}"**. The other
chapters are being built in parallel.

Start by reading the shared guide; it is binding: {{absolute path}}/GUIDE.md
Working directory: {{absolute path of FILM}}
Your scene file: scenes/sNN_<slug>.py (class `Clip`). Render with `./render.sh sNN draft|preview`.
Your scratch folder: {{scratchpad}}/sNN/

## What this chapter must make the viewer understand
Guiding question (opening card): "{{question}}"
Takeaway (closing line, answers the question): "{{takeaway}}"
{{Two to four sentences: the idea, why it follows from the previous chapter, the target length.}}
{{What the previous chapter ended on and what the next one starts from.}}

## Storyboard (beats in order; refine the staging, keep the ideas and their order)
1. `open_chapter(self, NN, "{{title}}", {{ACCENT}}, question="{{question}}", part=PART[{{n}}])`.
2. **{{Beat name}}.** {{What appears, what it turns into, which bundle fields it draws, the caption.}}
…
k. **{{Payoff beat}}.** {{The transform that carries the idea, 2.5–3 s, then a hold.}}
n. `takeaway(self, "{{takeaway}}", {{ACCENT}}, old_caption=cap)`, a hold on {{the object the next
   chapter inherits}}, then `close_chapter(self)`.

## Things to get right
- {{Scale traps, orientation that must match the source figure, depth-sorting risks, text placement.}}

Follow the guide's workflow exactly (draft, contact sheet, critique, fix; at least two full review
passes; then preview and full-resolution stills). The film is judged on clarity for the newcomer,
smoothness, fidelity and crispness: a clip that is correct but rushed, muddy or cramped is
unfinished. End with the guide's report.
```

## Writing beats

- A beat names objects and transforms, and the bundle field behind every number: "the rose bars `W_stock(d)` (`D.forecast.stock`) lift and stack on the blue bars".
- Give the caption text for each beat, ten words at most, and the words that introduce each new symbol.
- Start from one concrete instance before the general case: one record, one row, one cohort. Name the instance and the field it comes from.
- Mark exactly one beat as the payoff and give it time.
- State orientation whenever the result must match the source figure: which axis runs right, which row is on top.
- Offer optional beats as optional: "include it only if it stays clean; a crisp chapter without it beats a crowded one with it".

## Chapter archetypes

| Archetype | Beats |
|---|---|
| **Basics** (first chapter) | film title; one record as the motif, defined on a `definition_card`; its outcomes, each a card and a colour; its clock (show what the clock skips, e.g. a counter frozen over a weekend); a few records in motion; the question the film answers |
| **Setting** | the population today as the motif; the cut between known and unknown; the first aggregate growing out of the motif; a roadmap of the parts ahead |
| **Tangent** | the idea the formula rests on, worked on a small motif population (a cohort of 100): count, divide by the right denominator ("by the 82 still open, not by 100"), chain the steps; the curve emerges from the population; only then the symbol and the formula |
| **Estimation** | real records lined up by the relevant clock; what is censored and why it still counts; count at one value, then all; the formula's terms fly out of the counts; the clean estimate and its meaning |
| **Conditional** | the population shrinks to those that survived to a given point; the same curve rescaled by that survival; the worked example from the bundle, equal to the model's own row |
| **3D construction** | one row in the level front view, where it is a 2D bar chart; tilt while the other rows rise into towers; light one row to read it; straight down, where the field is the heat-map of the source figure; rise again at the wall's scale; collapse onto the wall over 4–5 s; merge; turn the wall to face the camera as the 2D marginal chart |
| **Simple forecast** | history; the pattern made visible; fold into groups; the rule; tile the rule forward; a hint that reality scatters around it |
| **Payoff** | add the streams; the full formula; "what is this number?"; one realisation as unit dots; several realisations; a band whose mean lands on the model; what actually happened |
| **Finale** | rebuild the source figure panel by panel in the order the film taught it; show the flow through it one path at a time with operation glyphs; shrink to make room for the one-line formula, each term flashing with its panel; hold |

Two 3D constructions in one film use the same grammar, so they rhyme.
