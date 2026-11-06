#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import argparse
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


DEFAULT_CASES = ["1:1", "1:2", "1:3", "1:4", "1:5"]
MAX_STEP = 1000000

PLOT_ITEMS = {
    "density": {
        "key": "Density",
        "ylabel": "Density (g/cm³)",
        "out": "density.png",
    },
    "volume": {
        "key": "Volume",
        "ylabel": "Volume (Å³)",
        "out": "volume.png",
    },
    "temperature": {
        "key": "Temp",
        "ylabel": "Temperature (K)",
        "out": "temperature.png",
    },
    "potential_energy": {
        "key": "PotEng",
        "ylabel": "Potential energy (eV)",
        "out": "potential_energy.png",
    },
}


def read_lammps_log(log_path, max_step=MAX_STEP):
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

            step = int(values[headers.index("Step")])

            # 追加run 1000の部分は読まない
            if step > max_step:
                continue

            rows.append(values)

    if headers is None or len(rows) == 0:
        raise RuntimeError(f"No thermo data found: {log_path}")

    data = np.array(rows)
    col = {name: i for i, name in enumerate(headers)}

    # 同じStepが複数回ある場合は最後の行を残す
    step_idx = col["Step"]
    keep = {}
    for i, step in enumerate(data[:, step_idx].astype(int)):
        keep[step] = i

    data = data[list(keep.values())]
    data = data[np.argsort(data[:, step_idx])]

    return col, data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_dir", default=".", help="base directory")
    parser.add_argument("--paths", nargs="+", default=DEFAULT_CASES, help="case directories")
    parser.add_argument("--log_file", default="log.lammps", help="LAMMPS log filename")
    parser.add_argument("--out_dir", default="thermo", help="output directory")
    parser.add_argument("--x", default="Time", choices=["Time", "Step"], help="x axis")
    parser.add_argument("--max_step", type=int, default=MAX_STEP, help="maximum step to read")
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    out_dir = base_dir / args.out_dir
    out_dir.mkdir(exist_ok=True)

    all_data = {}

    for case in args.paths:
        log_path = base_dir / case / args.log_file
        print(f"Reading: {log_path}")
        col, data = read_lammps_log(log_path, max_step=args.max_step)
        all_data[case] = (col, data)

    for name, info in PLOT_ITEMS.items():
        plt.figure(figsize=(6.4, 4.8))

        for case in args.paths:
            col, data = all_data[case]

            if info["key"] not in col:
                print(f"skip {case}: {info['key']} not found")
                continue

            x = data[:, col[args.x]]
            y = data[:, col[info["key"]]]

            plt.plot(x, y, label=case)

            out_dat = out_dir / f"{name}_{case}.dat"
            np.savetxt(
                out_dat,
                np.column_stack([x, y]),
                header=f"{args.x} {info['key']}"
            )

        plt.xlabel("Time (ps)" if args.x == "Time" else "Step")
        plt.ylabel(info["ylabel"])
        plt.title(info["ylabel"])
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        out_png = out_dir / info["out"]
        plt.savefig(out_png, dpi=300)
        plt.close()

        print(f"Saved: {out_png}")

    print(f"Saved dat files in: {out_dir}")


if __name__ == "__main__":
    main()