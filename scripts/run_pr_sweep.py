#!/usr/bin/env python3
"""Run an NPR sweep and archive labeled plots/data for each case."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path


REPO_DIR = Path("/home/ads-user/openfoam/openfoam-axisymmetric-nozzle-portfolio")
TEMPLATE_CASE_DIR = REPO_DIR / "case"
CASES_DIR = REPO_DIR / "cases"

P_AMB = 101352.93
T0_ENGINE = 833.33
GAMMA = 1.4


def format_label(pr: float) -> str:
    return f"PR{pr:.1f}"


def replace_scalar(path: Path, key: str, value: float) -> None:
    text = path.read_text()
    pattern = rf"(^.*\b{re.escape(key)}\b\s*=\s*)([^;]+)(;)"
    replacement = rf"\g<1>{value:.10f}\3"
    new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected one replacement for {key} in {path}, found {count}")
    path.write_text(new_text)


def replace_uniform_value(path: Path, key: str, value: float) -> None:
    text = path.read_text()
    pattern = rf"(^\s*{re.escape(key)}\s+)(?:uniform\s+)?([^;]+)(;)"
    replacement = rf"\g<1>uniform {value:.10f}\3"
    new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected one replacement for {key} in {path}, found {count}")
    path.write_text(new_text)


def replace_uniform_vector(path: Path, key: str, value: tuple[float, float, float]) -> None:
    text = path.read_text()
    vector_text = f"({value[0]:.10f} {value[1]:.10f} {value[2]:.10f})"
    pattern = rf"(^\s*{re.escape(key)}\s+uniform\s+)(\([^)]+\))(\s*;)"
    replacement = rf"\g<1>{vector_text}\3"
    new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"Expected one replacement for {key} in {path}, found {count}")
    path.write_text(new_text)


def clone_case(run_case_dir: Path) -> None:
    if run_case_dir.exists():
        shutil.rmtree(run_case_dir)

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            path = Path(directory) / name
            if name in {"postProcessing", "dynamicCode", "visualization.foam"}:
                ignored.add(name)
            elif name.startswith("log."):
                ignored.add(name)
            elif name != "0" and path.is_dir() and re.fullmatch(r"\d+(\.\d+)?([eE][+-]?\d+)?", name):
                ignored.add(name)
        return ignored

    shutil.copytree(TEMPLATE_CASE_DIR, run_case_dir, ignore=ignore)


def set_pr(run_case_dir: Path, pr: float) -> None:
    p0 = P_AMB * pr
    replace_uniform_vector(run_case_dir / "0" / "U", "internalField", (17.013, 0.0, 0.0))
    replace_uniform_value(run_case_dir / "0" / "p", "p0", p0)
    replace_scalar(run_case_dir / "system" / "thrustBalance", "p0Engine", p0)
    replace_scalar(run_case_dir / "system" / "functions", "p0Engine", p0)


def latest_thrust_data(run_case_dir: Path) -> Path:
    candidates = sorted((run_case_dir / "postProcessing").glob("*/thrustBalance/data"))
    if not candidates:
        raise FileNotFoundError("No thrustBalance data found after the run")
    return candidates[-1]


def run_one(pr: float, end_time: float) -> None:
    label = format_label(pr)
    archive_root = CASES_DIR / label
    run_case = archive_root / "case"
    archive_images = archive_root / "images"
    archive_data = archive_root / "data"
    archive_logs = archive_root / "logs"

    clone_case(run_case)
    set_pr(run_case, pr)

    control = run_case / "system" / "controlDict"
    control_text = control.read_text()
    control_text = re.sub(r"(^\s*endTime\s+)([^;]+)(;)", rf"\g<1>{end_time:.8f}\3", control_text, flags=re.MULTILINE)
    control.write_text(control_text)

    log_file = run_case / "log.shockFluid"
    cmd = (
        "source /opt/openfoam13/etc/bashrc >/dev/null 2>&1 && "
        "blockMesh >/dev/null 2>&1 && "
        "foamRun -solver shockFluid"
    )
    with log_file.open("w") as fh:
        subprocess.run(["bash", "-lc", cmd], cwd=run_case, stdout=fh, stderr=subprocess.STDOUT, check=True)

    data_file = latest_thrust_data(run_case)
    archive_data.mkdir(parents=True, exist_ok=True)
    archive_images.mkdir(parents=True, exist_ok=True)
    archive_logs.mkdir(parents=True, exist_ok=True)
    shutil.copy2(data_file, archive_data / "thrustBalance.csv")
    shutil.copy2(log_file, archive_logs / "shockFluid.log")
    shutil.copytree(run_case / "system", archive_root / "system", dirs_exist_ok=True)
    shutil.copytree(run_case / "0", archive_root / "0", dirs_exist_ok=True)

    subprocess.run(
        [
            "python3",
            str(REPO_DIR / "scripts" / "plot_thrust_convergence.py"),
            "--data-file",
            str(data_file),
            "--label",
            label,
            "--output-dir",
            str(archive_images),
        ],
        cwd=REPO_DIR,
        check=True,
    )
    subprocess.run(
        [
            "python3",
            str(REPO_DIR / "scripts" / "render_mach.py"),
            "--label",
            label,
            "--case-dir",
            str(run_case),
            "--output-dir",
            str(archive_images),
        ],
        cwd=REPO_DIR,
        check=True,
    )

    print(f"{label}: completed")
    print(f"  log: {log_file}")
    print(f"  data: {archive_data / 'thrustBalance.csv'}")
    print(f"  plots: {archive_images / f'thrust_convergence_{label}.png'}")
    print(f"         {archive_images / f'mach_contours_{label}.png'}")
    print(f"         {archive_images / f'mach_contours_zoom_{label}.png'}")
    print(f"  case: {run_case}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--end-time", type=float, default=0.01)
    parser.add_argument("--prs", type=float, nargs="+", default=[1.5, 1.8, 2.2, 3.0])
    args = parser.parse_args()

    CASES_DIR.mkdir(parents=True, exist_ok=True)

    for pr in args.prs:
        run_one(pr, args.end_time)


if __name__ == "__main__":
    main()
