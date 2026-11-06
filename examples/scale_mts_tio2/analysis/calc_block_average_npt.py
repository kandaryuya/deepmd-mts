#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import numpy as np


DEFAULT_CASES = ["1:1", "1:2", "1:3", "1:4", "1:5"]

# 1 ns NPTの後半500 psを解析
START_TIME_PS = 500.0
END_TIME_PS = 1000.0
N_BLOCKS = 5

# Reviewer対応で重要な量を中心に設定
PROPERTIES = {
    "temperature": "Temp",
    "pressure": "Press",
    "potential_energy": "PotEng",
    "kinetic_energy": "KinEng",
    "total_energy": "TotEng",
    "volume": "Volume",
    "density": "Density",
}


def read_lammps_log(log_path):
    headers = None
    rows = []

    with open(log_path, "r") as f:
        for line in f:
            parts = line.split()

            if len(parts) >= 2 and parts[0] == "Step":
                headers = parts
                continue

            if headers is None:
                continue

            if len(parts) < len(headers):
                continue

            try:
                values = [float(x) for x in parts[:len(headers)]]
            except ValueError:
                continue

            rows.append(values)

    if headers is None or len(rows) == 0:
        raise RuntimeError(f"No thermo data found: {log_path}")

    data = np.array(rows)
    col = {name: i for i, name in enumerate(headers)}

    if "Step" not in col or "Time" not in col:
        raise RuntimeError(f"Step or Time column not found: {log_path}")

    # 同じStepが複数ある場合は最後の行を残す
    step_idx = col["Step"]
    keep = {}
    for i, step in enumerate(data[:, step_idx].astype(int)):
        keep[step] = i

    data = data[list(keep.values())]
    data = data[np.argsort(data[:, step_idx])]

    return col, data


def block_average(time, values, start_time, end_time, n_blocks):
    block_edges = np.linspace(start_time, end_time, n_blocks + 1)
    block_means = []

    for i in range(n_blocks):
        t0 = block_edges[i]
        t1 = block_edges[i + 1]

        if i < n_blocks - 1:
            mask = (time >= t0) & (time < t1)
        else:
            mask = (time >= t0) & (time <= t1)

        block_values = values[mask]

        if len(block_values) == 0:
            block_means.append(np.nan)
        else:
            block_means.append(np.mean(block_values))

    block_means = np.array(block_means, dtype=float)
    valid = np.isfinite(block_means)
    valid_block_means = block_means[valid]

    if len(valid_block_means) == 0:
        mean = np.nan
        se = np.nan
    elif len(valid_block_means) == 1:
        mean = valid_block_means[0]
        se = np.nan
    else:
        mean = np.mean(valid_block_means)
        se = np.std(valid_block_means, ddof=1) / np.sqrt(len(valid_block_means))

    return mean, se, block_means, block_edges


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_dir", default=".", help="base directory")
    parser.add_argument("--paths", nargs="+", default=DEFAULT_CASES, help="case directories")
    parser.add_argument("--log_file", default="log.lammps", help="LAMMPS log filename")
    parser.add_argument("--out_dir", default="block_average", help="output directory")
    parser.add_argument("--start_time", type=float, default=START_TIME_PS, help="start time in ps")
    parser.add_argument("--end_time", type=float, default=END_TIME_PS, help="end time in ps")
    parser.add_argument("--n_blocks", type=int, default=N_BLOCKS, help="number of blocks")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    out_dir = base_dir / args.out_dir
    out_dir.mkdir(exist_ok=True)

    summary_lines = []
    summary_lines.append(
        "# case property mean standard_error n_blocks start_time_ps end_time_ps"
    )

    for case in args.paths:
        log_path = base_dir / case / args.log_file
        print(f"Reading: {log_path}")

        col, data = read_lammps_log(log_path)
        time = data[:, col["Time"]]

        case_dir = out_dir / case
        case_dir.mkdir(exist_ok=True)

        for prop_name, lammps_key in PROPERTIES.items():
            if lammps_key not in col:
                print(f"skip {case}: {lammps_key} not found")
                continue

            values = data[:, col[lammps_key]]

            mean, se, block_means, block_edges = block_average(
                time=time,
                values=values,
                start_time=args.start_time,
                end_time=args.end_time,
                n_blocks=args.n_blocks,
            )

            summary_lines.append(
                f"{case} {prop_name} {mean:.10g} {se:.10g} "
                f"{args.n_blocks} {args.start_time:.3f} {args.end_time:.3f}"
            )

            block_out = case_dir / f"{prop_name}_blocks.dat"
            with open(block_out, "w") as f:
                f.write("# block start_time_ps end_time_ps block_mean\n")
                for i, bm in enumerate(block_means):
                    f.write(
                        f"{i+1} {block_edges[i]:.6f} "
                        f"{block_edges[i+1]:.6f} {bm:.10g}\n"
                    )

    summary_path = out_dir / "summary_mean_se.dat"
    summary_path.write_text("\n".join(summary_lines) + "\n")

    print(f"Saved: {summary_path}")
    print(f"Saved block files in: {out_dir}")


if __name__ == "__main__":
    main()