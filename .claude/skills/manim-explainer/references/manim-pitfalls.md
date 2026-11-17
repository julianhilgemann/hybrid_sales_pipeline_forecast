# Manim pitfalls

Each entry was hit and solved while building a seven-chapter film with Manim Community 0.22.1 and the Cairo renderer. Helpers named here live in `common.py`.

## Any scene

| Symptom | Cause | Do this |
|---|---|---|
| y-axis drawn in the middle of the chart | `Axes` puts the y-axis at x = 0 whenever 0 is inside `x_range` | plot against `x - x_min` and write the tick labels by hand |
| two captions superimposed for half a second | cross-fading the old and new line | `swap_caption(scene, old, "new text")`: old out, then new in |
| a faded-out object reappears | a second `FadeOut` on it re-adds it to the scene | keep track of what is on screen; fade each object once |
| hundreds of moving marks render slowly | `always_redraw` rebuilds every mobject every frame | precompute every mark, drive one `ValueTracker`, and let one updater move end points and restyle only on a state change |
| a heat-map animates slowly | one animation per cell | animate rows or columns: `VGroup`s of cells in a `LaggedStart` |
| `Arrow(..., tip_width=…)` raises | not an `Arrow` argument in 0.22 | `max_tip_length_to_length_ratio` |
| cannot colour or move one term of a formula | the term is inside one TeX string | pass the terms to `MathTex` as separate strings; this works inside `\frac` too |
| a symbol should fly out of its object | | `TransformFromCopy(label_on_chart, term_in_formula)` in 2D scenes |
| data fills a third of its axis | range sized for something that appears later | start with a tight range and animate the rescale (bars shrink, old ticks fade, new ticks arrive) when the larger data arrives |

## 3D scenes (Cairo)

Cairo paints polygons back to front. Every rule below follows from how it chooses that order.

| Symptom | Cause | Do this |
|---|---|---|
| a tall ribbon pops in front of a nearer short one | shaded mobjects sort by bounding-box centre | build ribbons with `ribbon_3d` (`DepthPoly` / `DepthPath` sort by floor position) and add them far to near |
| axes, lines or tiles always draw on top of the ribbons | mobjects without `shade_in_3d` are painted after every shaded one | call `set_shade_in_3d(True)` on 3D lines that must pass behind; bring unshaded floor tiles in only while ribbons fade or lie flat |
| far-to-near order breaks during a staggered entrance | `LaggedStart` re-adds its group on top of the scene | one animation per mobject with `rate_func=delayed(start, length)` |
| a fade passed to `move_camera(added_anims=…)` lasts the whole move | `move_camera` applies its `run_time` to every added animation | time it inside the move with `delayed(start, length)` |
| the floor swings off-frame or into the caption mid-move | phi and theta change faster than the framing | check a mid-move frame; dip the zoom mid-move or move `frame_center` with it |
| text tilts with the scene | it lives in 3D space | `fix_in_frame(scene, mob)` before animating it in |
| ghost copies of text float in 3D after a camera move | `TransformFromCopy` and `FadeTransform` create copies that are not pinned | in 3D use plain fades on pinned text, or do the transform while the camera is still flat |
| a group of 3D-anchored labels drifts | `add_fixed_orientation_mobjects(group)` positions by the group's centre | add labels one by one, each with its own anchor point |
| points you project yourself land in the wrong place | the camera keeps a stale rotation matrix after `set_camera_orientation` | `self.renderer.camera.reset_rotation_matrix()` before projecting |
| `bars()` or `curve()` misplace shapes on rotated axes | they rely on unit sizes and aligned edges | build the chart flat, then rotate the whole group: `mob.rotate(PI / 2, RIGHT, about_point=ORIGIN)` lifts a screen-plane chart into the x–z plane |
| a stack of translucent ribbons looks muddy | fills accumulate | faint sheets (opacity about 0.3), bright edges, near-empty series fainter still |
| dozens of crossing series read as a wireframe mesh | fills and vertical risers | thin lines only, depth-graded: near ones bright and thick, far ones dim and thin |
| render time explodes | too many polygons sorted per frame | stay under about 900 3D polygons on screen; fade one family out as another comes in |

## Patterns that worked

- **Flat to 3D to flat.** A `ThreeDScene` starts at phi 0, theta −90°, which is an ordinary 2D view. Build the flat chart first, tilt the camera for the 3D beat, return to flat. The viewer keeps the same axes throughout.
- **Straight down is the heat-map.** Stand ribbons on the floor, glide to `CAM_TOP` while `floor_tiles_3d` fade in, and the surface becomes the flat heat-map of the source figure.
- **Collapse onto the wall.** To show a sum over one axis, slide the ribbons back along that axis, staggered, over 2.5–3 s, and stack them on the back wall. Give the wall its own labelled scale: marginals are larger than cells.
- **Collapse copies, never originals.** When a panel "pours" into another, animate copies that first squash in place into chips the size of the result, then travel. The source stays visible and nothing large crosses other data.
- **Camera-facing label at a 3D point**, with a fixed screen offset so it never drifts into the data:

  ```python
  def anchor(self, mob, point, offset=ORIGIN):
      A = np.array(point, dtype=float)
      mob.move_to(A + np.array(offset, dtype=float))
      self.add_fixed_orientation_mobjects(mob, center_func=lambda: A)
      self.remove(mob)
      return mob
  ```
