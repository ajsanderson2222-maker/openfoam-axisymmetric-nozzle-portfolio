# Geometry

The first-pass geometry is defined directly in `case/system/blockMeshDict`.

Planned use for this directory:

- CAD exports if the nozzle profile is later refined,
- sketches or notes for the convergent section,
- references for any future nozzle lip or external shape updates.

The current mesh is a validated first pass built from the requested nozzle dimensions:

- 4 in radius nozzle,
- 12 in total axial length,
- 20 percent area reduction over the last 2 in,
- freestream box sized at `10x` nozzle length by `10x` nozzle radius,
- lower axis / upper slip-style 2D extrusion with a duplicated wall split upstream of the exit.
