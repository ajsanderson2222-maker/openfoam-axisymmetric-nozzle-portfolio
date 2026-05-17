# CLAUDE.md

This repository is being built as an OpenFOAM portfolio case for an axisymmetric nozzle.

## Current focus

- geometry and mesh creation first,
- solver, boundary conditions, and thrust post-processing later,
- keep the structure compact and readable.

## Initial geometry intent

- 2D axisymmetric wedge,
- straight nozzle section,
- convergent end section,
- upstream and downstream farfield blocks.

## Solver direction

- use the current `shockFluid` solver path for compressible, shock-capable flow,
- keep the current mesh unchanged until the baseline run is stable,
- refine only after the solver case is working.

## Post-processing direction

- write `MachNo` automatically at write times,
- capture inlet momentum, inlet pressure, wall pressure, and wall shear for `T_CFD`,
- leave `T_ideal(PR)` as the next step after the CFD thrust balance is in place.
