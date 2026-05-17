#!/usr/bin/env python3
"""Render the actual nozzle mesh layout from the block topology."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle


def draw_rect_grid(ax, x0, x1, y0, y1, nx, ny, color="#dbe3ec", lw=0.45, alpha=0.95):
    for i in range(1, nx):
        x = x0 + (x1 - x0) * i / nx
        ax.plot([x, x], [y0, y1], color=color, lw=lw, alpha=alpha, zorder=3)
    for j in range(1, ny):
        y = y0 + (y1 - y0) * j / ny
        ax.plot([x0, x1], [y, y], color=color, lw=lw, alpha=alpha, zorder=3)


def draw_tapered_grid(ax, bl, br, tr, tl, nx, ny, color="#dbe3ec", lw=0.45, alpha=0.95):
    for i in range(1, nx):
        t = i / nx
        xb = bl[0] + t * (br[0] - bl[0])
        yb = bl[1] + t * (br[1] - bl[1])
        xt = tl[0] + t * (tr[0] - tl[0])
        yt = tl[1] + t * (tr[1] - tl[1])
        ax.plot([xb, xt], [yb, yt], color=color, lw=lw, alpha=alpha, zorder=3)
    for j in range(1, ny):
        s = j / ny
        xl = bl[0] + s * (tl[0] - bl[0])
        yl = bl[1] + s * (tl[1] - bl[1])
        xr = br[0] + s * (tr[0] - br[0])
        yr = br[1] + s * (tr[1] - br[1])
        ax.plot([xl, xr], [yl, yr], color=color, lw=lw, alpha=alpha, zorder=3)


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    out = repo / "images" / "axi_nozzle_mesh.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    # Geometry in inches, matching blockMeshDict.
    x0, x1, x2, x3 = 0.0, 10.0, 12.0, 120.0
    y0, y1, y2, y3 = 0.0, 4.0, 3.577708764, 40.0

    fig, ax = plt.subplots(figsize=(13.5, 7.5), constrained_layout=True)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    # Domain fill.
    ax.add_patch(Rectangle((x0, y0), x3 - x0, y3 - y0, facecolor="#1e6686", edgecolor="#123748", linewidth=2.2, zorder=1))

    # Mesh blocks.
    blocks = [
        ((x0, y0), (x1, y0), (x1, y1), (x0, y1), 28, 16),
        ((x0, y1), (x1, y1), (x1, y3), (x0, y3), 28, 36),
        ((x1, y0), (x2, y0), (x2, y2), (x1, y1), 10, 16),
        ((x1, y1), (x2, y2), (x2, y3), (x1, y3), 10, 36),
        ((x2, y0), (x3, y0), (x3, y2), (x2, y2), 72, 16),
        ((x2, y2), (x3, y2), (x3, y3), (x2, y3), 72, 36),
    ]

    # Draw block outlines and grid lines.
    for bl, br, tr, tl, nx, ny in blocks:
        poly = Polygon([bl, br, tr, tl], closed=True, fill=False, edgecolor="#173445", linewidth=1.6, zorder=4)
        ax.add_patch(poly)
        if abs(bl[1] - br[1]) < 1e-9 and abs(tl[1] - tr[1]) < 1e-9 and abs(bl[0] - tl[0]) < 1e-9:
            draw_rect_grid(ax, bl[0], br[0], bl[1], tl[1], nx, ny)
        else:
            draw_tapered_grid(ax, bl, br, tr, tl, nx, ny)

    # Highlight the actual nozzle wall path shared by the upstream blocks.
    ax.plot([x0, x1, x2], [y1, y1, y2], color="black", linewidth=2.0, zorder=6)

    # Engine inlet notch at lower left, matching the reference composition.
    ax.plot([0.0, 0.0, 1.2, 1.2, 1.45], [0.0, 0.18, 0.18, 0.42, 0.42], color="#222222", linewidth=1.8, zorder=7)

    # Labels.
    ax.text(60.0, 41.3, "Slip Wall", ha="center", va="bottom", fontsize=16, color="#111111")
    ax.text(-1.7, 20.0, "Freestream Inlet", ha="right", va="center", fontsize=15, color="#111111")
    ax.text(121.8, 20.0, "Freestream Outlet", ha="left", va="center", fontsize=15, color="#111111")
    ax.text(0.8, 1.0, "Engine Inlet", ha="left", va="center", fontsize=15, color="#111111")
    ax.text(60.0, -3.0, "Axis of Rotation", ha="center", va="top", fontsize=15, color="#111111")

    ax.set_xlim(-15, 135)
    ax.set_ylim(-6, 46)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.savefig(out, dpi=220, facecolor=fig.get_facecolor())
    print(out)


if __name__ == "__main__":
    main()
