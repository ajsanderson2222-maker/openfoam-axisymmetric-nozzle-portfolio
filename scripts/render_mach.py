#!/usr/bin/env python3
"""Render Mach contours from the latest OpenFOAM timestep."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pyvista as pv


def read_end_time(case_dir: Path) -> float | None:
    control = case_dir / "system" / "controlDict"
    text = control.read_text()
    match = re.search(r"^\s*endTime\s+([0-9.eE+-]+)\s*;", text, re.MULTILINE)
    return float(match.group(1)) if match else None


def load_latest_internal_mesh(case_dir: Path) -> pv.UnstructuredGrid:
    foam = case_dir / "visualization.foam"
    foam.touch(exist_ok=True)

    reader = pv.OpenFOAMReader(str(foam))
    end_time = read_end_time(case_dir)
    if end_time is None:
        time_value = reader.time_values[-1]
    else:
        candidates = [t for t in reader.time_values if t <= end_time + 1e-9]
        time_value = candidates[-1] if candidates else reader.time_values[-1]
    reader.set_active_time_value(time_value)
    blocks = reader.read()
    return blocks["internalMesh"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="PR2.0")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/ads-user/openfoam/openfoam-axisymmetric-nozzle-portfolio/images"),
    )
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    case_dir = repo / "case"
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    run_label = args.label

    grid = load_latest_internal_mesh(case_dir)
    centers = grid.cell_centers().points
    x = centers[:, 0] / 0.0254
    y = centers[:, 1] / 0.0254

    U = np.asarray(grid.cell_data["U"])
    T = np.asarray(grid.cell_data["T"])
    speed = np.linalg.norm(U, axis=1)

    gamma = 1.4
    R = 287.0
    mach = speed / np.sqrt(gamma * R * T)
    finite = np.isfinite(x) & np.isfinite(y) & np.isfinite(mach)
    x = x[finite]
    y = y[finite]
    mach = mach[finite]

    levels = np.linspace(0.0, max(0.5, float(np.nanmax(mach))), 28)

    # Domain outline and nozzle wall sketch for orientation.
    x0, x1, x2, x3 = 0.0, 10.0, 12.0, 480.0
    y0, y1, y2, y3 = 0.0, 4.0, 3.577708764, 160.0

    def render(out_path: Path, xlim: tuple[float, float], ylim: tuple[float, float], title: str) -> None:
        fig, ax = plt.subplots(figsize=(13.5, 7.0), constrained_layout=True)
        ax.set_facecolor("#f7f7f5")
        contour = ax.tricontourf(x, y, mach, levels=levels, cmap="turbo", extend="max")
        ax.tricontour(x, y, mach, levels=levels[::2], colors="k", linewidths=0.35, alpha=0.3)

        cbar = fig.colorbar(contour, ax=ax, pad=0.015)
        cbar.set_label("Mach number", rotation=90)

        ax.plot([x0, x3, x3, x0, x0], [y0, y0, y3, y3, y0], color="#111111", lw=1.0, alpha=0.5)
        ax.plot([x0, x1, x2], [y1, y1, y2], color="#111111", lw=2.0)
        ax.plot([x0, x0, 1.2, 1.2, 1.45], [0.0, 0.18, 0.18, 0.42, 0.42], color="#111111", lw=1.4)

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.set_aspect("equal")
        ax.set_xlabel("Axial distance [in]")
        ax.set_ylabel("Radial distance [in]")
        ax.set_title(title)

        fig.savefig(out_path, dpi=220)
        plt.close(fig)
        print(out_path)

    render(
        out_dir / f"mach_contours_{run_label}.png",
        (0, 480),
        (0, 160),
        f"Axisymmetric nozzle Mach contours at latest time ({run_label})",
    )
    render(
        out_dir / f"mach_contours_zoom_{run_label}.png",
        (0, 40),
        (0, 15),
        f"Axisymmetric nozzle Mach contours, bottom-left zoom ({run_label})",
    )


if __name__ == "__main__":
    main()
