# Anti-slop: how to not look like AI

"Don't look like AI" is useless as an instruction because it names no behavior. AI slop
is a specific set of habits a model falls into when it has no point of view. This file
turns "avoid slop" into concrete, checkable rules. Put the relevant **forbid** lines into
every master prompt, aim for the **aim-for** qualities, and run the checklist in self-review.

## Forbid (write these as explicit "never" lines in the prompt)

- **Glossy plastic 3D blobs.** No rounded, candy-coated render-engine shapes floating with
  soft studio reflections. They read as a 2021 app illustration, not a brand.
- **Unmotivated purple/blue gradients on white.** The default "tech" wash. If a gradient is
  not justified by a real light source or material, cut it.
- **Dead-center symmetry.** Subject parked in the exact middle, mirrored left-to-right. It
  signals "no compositional decision was made."
- **Fake bokeh filler.** Out-of-focus circles and sparkles used to fill empty space instead
  of real negative space or real depth.
- **Blown-out HDR highlights.** Over-cooked tone-mapping where every surface glows. Kills
  material truth and mood.
- **Smeared or misspelled text.** Warped letterforms, invented glyphs, garbled words. The
  single fastest "this is AI" tell.
- **Generic stock-photo staging.** Handshakes, headset call-center smiles, diverse-team-
  around-a-laptop, lightbulb = idea. Cliché blocking with no specificity.
- **Particle / circuit / hexagon clutter.** Floating dots, glowing circuit traces, hex grids,
  network-node confetti standing in for "technology."
- **Heavy bevels and skeuomorphic glass.** Thick drop shadows, beveled buttons, frosted-glass
  panels layered for fake depth.
- **Uncanny over-smooth mascots.** Plasticky characters with dead eyes and airbrushed skin.

## Aim for (the qualities that replace each forbidden habit)

- **One clear focal element**, placed off-center with deliberate asymmetry and real negative
  space around it. The eye should know where to land.
- **A dominant color with one decisive accent.** Not a rainbow, not a gradient soup — one
  color owns the frame, one accent punctuates it.
- **One believable, named light source.** "Low side light from a left window," "overhead
  noon sun." Name it so shadows and falloff stay consistent.
- **One shared material across the set.** Matte paper, brushed metal, raw ceramic — pick one
  and let every slide live in the same physical world.
- **Type treated as design**, with real hierarchy (one dominant size, clear secondary, quiet
  tertiary), not a caption dropped on top as an afterthought.
- **Texture and depth from craft, not particles.** Grain, paper tooth, honest shadow, layered
  physical objects — depth earned by the scene, not sprinkled on.

## Self-review checklist (used in step 7)

Judge every generated frame against these. Any "no" is a reshoot candidate.

1. Is there one obvious focal point, placed off dead-center?
2. Does one color dominate, with a single accent — no gradient mush?
3. Is the light direction consistent and believable across the set?
4. Do all slides share one material / physical world?
5. Is any in-image text spelled correctly and the *right* words (not just legible)?
6. Are the numbers/data exactly correct (verify literally, legible ≠ correct)?
7. Is the frame free of particles, fake bokeh, circuit/hex clutter, and glassy bevels?
8. Does it look like a decision was made — or like a default was accepted?
