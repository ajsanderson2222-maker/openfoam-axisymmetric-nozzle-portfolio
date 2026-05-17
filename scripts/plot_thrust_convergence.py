#!/usr/bin/env python3

import argparse
from pathlib import Path

import matplotlib.pyplot as plt


CASE_DIR = Path("/home/ads-user/openfoam/openfoam-axisymmetric-nozzle-portfolio/case")
POST_DIR = CASE_DIR / "postProcessing"
def read_table(path: Path):
    rows = []
    with path.open() as fh:
        header = fh.readline().strip().split()
        for line in fh:
            if not line.strip():
                continue
            parts = line.split()
            rows.append(dict(zip(header, parts)))
    return rows


def find_latest_data_file() -> Path:
    candidates = sorted(POST_DIR.glob("*/thrustBalance/data"))
    if not candidates:
        raise FileNotFoundError(f"No thrustBalance data found under {POST_DIR}")
    return candidates[-1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-file", type=Path)
    parser.add_argument("--label", default="PR2.0")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("/home/ads-user/openfoam/openfoam-axisymmetric-nozzle-portfolio/images"),
    )
    args = parser.parse_args()

    data_file = args.data_file or find_latest_data_file()
    rows = read_table(data_file)
    step = [int(r["#step"]) for r in rows]
    cfd = [float(r["T_CFD360"]) for r in rows]
    ideal = [float(r["T_ideal360"]) for r in rows]
    cfg = [float(r["Cfg"]) for r in rows]

    fig, ax1 = plt.subplots(figsize=(10, 5.5), dpi=160)

    ax1.plot(step, cfd, color="#0b6e4f", lw=1.8, label="T_CFD360")
    ax1.plot(step, ideal, color="#1f77b4", lw=1.8, label="T_ideal360")
    ax1.set_xlabel("Iteration")
    ax1.set_ylabel("Thrust [N]")
    ax1.grid(True, alpha=0.25)

    ax2 = ax1.twinx()
    ax2.plot(step, cfg, color="#b23a48", lw=1.6, label="Cfg")
    ax2.set_ylabel("Cfg = T_CFD / T_ideal")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="best", frameon=False)

    title = (
        f"Thrust convergence from iteration {step[0]} to {step[-1]} "
        f"({len(step)} samples, {args.label})"
    )
    ax1.set_title(title)

    fig.tight_layout()
    out_file = args.output_dir / f"thrust_convergence_{args.label}.png"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_file)

    print(f"Read {data_file}")
    print(f"Wrote {out_file}")
    print(f"Samples: {len(step)}")
    print(f"First: step={step[0]} T_CFD360={cfd[0]:.6f} T_ideal360={ideal[0]:.6f} Cfg={cfg[0]:.6f}")
    print(f"Last:  step={step[-1]} T_CFD360={cfd[-1]:.6f} T_ideal360={ideal[-1]:.6f} Cfg={cfg[-1]:.6f}")
    print(f"Delta: T_CFD360={cfd[-1]-cfd[0]:.6f} T_ideal360={ideal[-1]-ideal[0]:.6f} Cfg={cfg[-1]-cfg[0]:.6f}")


if __name__ == "__main__":
    main()
