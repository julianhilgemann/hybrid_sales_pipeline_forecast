# Manim pitfalls

Each entry was hit and solved while building two films (seven and eleven chapters) with Manim Community 0.22.1 and the Cairo renderer. Helpers named here live in `common.py`.

## Any scene

| Symptom | Cause | Do this |
|---|---|---|
| a name imported at the top of a scene now means something else | `from common import *` (with manim's own star export inside it) replaces names imported before it | import a scene's own modules after the star import, or qualify them (`collections.Counter`); give new helpers names no common library uses |
| a `delayed(...)` timing is silently ignored | `self.play(..., rate_func=X)` replaces every animation's own rate function | set rate functions per animation (`FadeIn(m, rate_func=...)`, `m.animate(rate_func=...)`); leave `rate_func` off `play` |
| a panel faded in covers the numbers flown onto it | `FadeIn` adds its mobject after the non-introducing animations of the same `play`, so it paints on top whatever the argument order | `set_z_index(-1)` on the panel or `set_z_index(2)` on what must stay in front |
| a group's updater never runs | a `LaggedStart` over a group's members adds the members, not the group | after it, `self.remove(*group); self.add(group)` |
| copies stay on screen after `self.remove(copies)` | the animation added the members one by one | `self.remove(*copies)` |
| a whole heat-map fades back in on top of everything | it was animated in by rows (only the row groups are in the scene); fading the grid re-adds it | animate rows out too, or re-add the panels in a fixed draw order |
| `SurroundingRectangle(grid)` balloons | it encloses dots that have moved away from the grid | surround a fixed reference shape the size of the grid |
| y-axis drawn in the middle of the chart, or through bar 0 | `Axes` puts the y-axis at x = 0 whenever 0 is inside `x_range` | `Chart` with `x_range=(-0.6, n + 0.6)` |
| an axis must rescale or change meaning mid-chapter | `Axes` and `tick_labels` fix their range | `Chart.with_range`, Transform each mark into its new build, swap tick labels old out then new in |
| data fills a third of its axis | range sized for something that appears later | start with a tight range and animate the rescale when the larger data arrives |
| two captions superimposed for half a second | cross-fading the old and new line | `swap_caption(scene, old, "new")`: old out, then new in |
| the caption cannot change while the visual it describes moves | `swap_caption` plays on its own | `new, anims = caption_swap(scene, old, "new", run_time)` and play `anims` inside the move; or `swap_caption(scene, old, "new", *exits)` to let dimming or a leaving panel ride with the old line |
| a faded-out object reappears | a second `FadeOut` on it re-adds it to the scene | keep track of what is on screen; fade each object once |
| hundreds of moving marks render slowly | `always_redraw` rebuilds every mobject every frame | precompute every mark, drive one `ValueTracker`, and let one updater move end points and restyle only on a state change |
| a heat-map animates slowly | one animation per cell | animate rows or columns: `VGroup`s of cells |
| `Arrow(..., tip_width=…)` raises | not an `Arrow` argument in 0.22 | `max_tip_length_to_length_ratio` |
| a symbol should fly out of its object | | `TransformFromCopy(label_on_chart, term_in_formula)` in 2D scenes |

## Text and numbers

| Symptom | Cause | Do this |
|---|---|---|
| cannot colour or move one term of a formula | the term is inside one TeX string | pass the terms to `MathTex` as separate strings; this works inside `\frac` too |
| cannot colour one word of a sentence | the template has no `xcolor` | `text_line(["the kernel ", "$k(a)$", " peaks"], colors=[None, AMBER, None])`; `caption`, `takeaway` and `definition_card` body lines take the same parts |
| words run together | `Tex("a", "b")` joins its parts with no space | put the spaces inside the parts |
| a counter switches to Computer Modern digits | `Integer(mob_class=Tex)` rebuilds its digits in the default font on `set_value` | `TexCounter` |
| old digits linger under the new ones | Cairo draws the family list captured when the `play` started | `TexCounter` blanks the old glyphs' points |
| `zip() argument 2 is longer than argument 1` | `FadeIn` of a Tex whose updater `become`s a version with a different glyph count | fade it in before attaching the updater, or use `TexCounter` |
| digits in two fonts | `tick_labels` and `Chart` ticks are `MathTex` (Computer Modern), annotations `Tex` (the text font) | keep that split film-wide: tick numbers in maths, numbers in sentences in text |

## 3D scenes (Cairo)

Cairo paints polygons back to front. Most rules below follow from how it chooses that order.

| Symptom | Cause | Do this |
|---|---|---|
| towers freeze, then pop into place at the end of a play; floor lines paint over towers | a play that animates only a caption treats the rest as static background | `setup_3d(self)` as the first line: its host mobject always moves, so every frame redraws and re-sorts (about 20 s more per draft) |
| header, captions and formulas sit offset for the whole clip | `frame_center` was set before the first frame rendered; Cairo keeps that offset for pinned overlays | move `frame_center` only after `open_chapter` |
| fades and copies of floor lines are slow or fail | the camera stored on an instance is deep-copied by every fade, copy or `.animate` | keep the camera on the class (`FloorLine` does); never store it on a mobject |
| a tall ribbon pops in front of a nearer short one | shaded mobjects sort by bounding-box centre | `ribbon_3d` (`DepthPoly` / `DepthPath` sort by floor position); add far to near |
| axes, lines or tiles always draw on top of the 3D content | mobjects without `shade_in_3d` paint after every shaded one | `FloorLine` / `floor_grid` / `FloorPoly` for anything on the floor or behind towers; `set_shade_in_3d(True)` on other 3D lines that must pass behind |
| far-to-near order breaks during a staggered entrance | `LaggedStart` re-adds its group on top of the scene | one animation per mobject with `rate_func=delayed(start, length)`, or `HeatTowers.lift(order=..., lag=...)` |
| a fade passed to a camera move lasts the whole move | the move's `run_time` applies to every added animation | time it inside the move with `delayed(start, length)` |
| the floor swings off-frame or through the formula mid-move | phi, theta and framing change at the same pace | `cam_to(..., zoom_dip=0.1, fc_lead=0.6)`; check a mid-move frame; `hide_during` for labels that would sweep through text |
| text tilts with the scene | it lives in 3D space | `fix_in_frame(scene, mob)` before animating it in |
| ghost copies of a formula float in 3D after a transform | Transforms add pieces that are not pinned (`TransformFromCopy`, `FadeTransform`, a Transform between different glyph counts) | `pinned(scene, Transform(a, b))`; where a symbol changes, cross-fade instead |
| a bar morphing into a row of dots leaves unpinned dots | one pinned mobject became many pieces | split it into as many pinned slices first, then transform slice to dot |
| a group of 3D-anchored labels drifts | `add_fixed_orientation_mobjects(group)` positions by the group's centre | `pin_label` each label with its own anchor point |
| tick labels stay behind when an axis slides or rescales | fixed anchors | `move_pins(scene, [(label, new_point, new_offset), …])` inside the move |
| points you project yourself land in the wrong place | the camera keeps a stale rotation matrix after `set_camera_orientation` | `self.renderer.camera.reset_rotation_matrix()` before projecting |
| `bars()` or `curve()` misplace shapes on rotated axes | they rely on unit sizes and aligned edges | build the chart flat, then rotate the whole group: `mob.rotate(PI / 2, RIGHT, about_point=ORIGIN)` lifts a screen-plane chart into the x–z plane |
| most heat cells are nearly black | a few large cells set `vmax` and the ramp is linear | `HeatTowers(..., gamma=0.6)`; give any colour bar the same mapping |
| the collapse onto the wall is over before the eye finds it | per-tower easing on top of the play's easing squeezes each slide into about half a second | the toolkit's `collapse` plays linearly with `lag=0.35`: give it 4–5 s |
| a bright rim at the foot of every stacked bar | the smallest towers have only a top face | `T.merge(scene, color)` swaps the finished stacks for solid bars |
| a stack of translucent ribbons looks muddy | fills accumulate | faint sheets (opacity about 0.3), bright edges, near-empty series fainter still |
| dozens of crossing series read as a wireframe mesh | fills and vertical risers | thin lines only, depth-graded: near ones bright and thick, far ones dim and thin |
| render time explodes | too many polygons sorted per frame | stay under about 1000 faces on screen; fade one family out as another comes in |

## Patterns that worked

- **The tower grammar.** In `CAM_FRONT` one raised row of `HeatTowers` is a 2D bar chart; tilt while the other rows rise; light one row with `tint` to read it; straight down (`CAM_TOP`) the flattened field is the heat-map of the source figure; rise again at the wall's scale; `collapse` stacks each column on the wall, where the stack is the column's sum; `merge`; turn the wall to face the camera and it is the 2D marginal chart. The bars are literally made of the cells, so the viewer never loses the thread.
- **Flat to 3D to flat.** A `ThreeDScene` starts at phi 0, theta −90°, which is an ordinary 2D view. Build the flat chart first, tilt for the 3D beat, return to flat.
- **Collapse copies, never originals.** When a 2D panel "pours" into another, animate copies that first squash in place into chips the size of the result, then travel. The source stays visible and nothing large crosses other data.
- **The motif population.** A 10 × 10 `dot_grid` whose counts are rounded expectations of the real rates teaches hazards, survival and conditioning before any formula: dots resolve day by day, the denominator is visibly "those still open", and a conditional is the grid shrinking to its survivors.
- **A living hold.** In 3D, a slow `drift` of a few degrees during a long caption keeps the scene alive without stealing attention.
- **Hide what would sweep.** `hide_during` fades labels out for the middle of a camera move and back in after, instead of letting them cross the formula.
