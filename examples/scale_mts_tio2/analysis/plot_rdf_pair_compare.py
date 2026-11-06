#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

from ovito.io import import_file
from ovito.modifiers import LoadTrajectoryModifier, CoordinationAnalysisModifier


def make_pair_labels(type_map):
    labels = []
    for i, a in enumerate(type_map):
        for b in type_map[i:]:
            labels.append(f"{a}-{b}")
    return labels


def calc_partial_rdf(case_dir, dump_file, data_file, cutoff, bins):
    dump_path = case_dir / dump_file
    data_path = case_dir / data_file

    if not dump_path.exists():
        raise FileNotFoundError(f"dump file not found: {dump_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"data file not found: {data_path}")

    pipeline = import_file(str(data_path))

    traj = LoadTrajectoryModifier()
    traj.source.load(str(dump_path))
    pipeline.modifiers.append(traj)

    pipeline.modifiers.append(
        CoordinationAnalysisModifier(
            cutoff=cutoff,
            number_of_bins=bins,
            partial=True
        )
    )

    nframes = pipeline.source.num_frames
    if nframes == 0:
        raise RuntimeError(f"No frames found in {dump_path}")

    rdf_sum = None
    r = None

    for frame in range(nframes):
        data = pipeline.compute(frame)
        table = data.tables["coordination-rdf"]
        arr = table.xy()

        r = arr[:, 0]
        y = arr[:, 1:]

        if rdf_sum is None:
            rdf_sum = np.zeros_like(y)

        rdf_sum += y

    rdf_avg = rdf_sum / nframes
    return r, rdf_avg, nframes


def main():
    parser = argparse.ArgumentParser(
        description="Compare partial RDFs for TiO2 cases: 4, 4-6, 6"
    )
    parser.add_argument(
        "--base_dir",
        default=".",
        help="base directory. Run from 01_baseline, so default is current directory"
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        default=["1:1", "1:2", "1:3", "1:4", "1:5"],
        help="case directories to compare"
    )
    parser.add_argument(
        "--dump_file",
        default="tio2_anatase_additional_step1000.dump",
        help="LAMMPS dump file name in each case directory"
    )
    parser.add_argument(
        "--data_file",
        default="tio2_anatase_12000.lmp",
        help="LAMMPS data file name in each case directory"
    )
    parser.add_argument(
        "--type_map",
        nargs="+",
        default=["Ti", "O"],
        help="atom type labels in LAMMPS type order"
    )
    parser.add_argument(
        "--cutoff",
        type=float,
        default=8.0,
        help="RDF cutoff distance in Angstrom"
    )
    parser.add_argument(
        "--bins",
        type=int,
        default=200,
        help="number of RDF bins"
    )
    parser.add_argument(
        "--out_dir",
        default="rdf_pair_compare",
        help="output directory"
    )
    parser.add_argument(
        "--prefix",
        default="additional_",
        help="output file prefix"
    )
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()
    out_dir = base_dir / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pair_labels = make_pair_labels(args.type_map)

    results = {}
    frame_counts = {}

    for case in args.paths:
        case_dir = base_dir / case
        print(f"Processing: {case_dir}")

        r, rdf_avg, nframes = calc_partial_rdf(
            case_dir=case_dir,
            dump_file=args.dump_file,
            data_file=args.data_file,
            cutoff=args.cutoff,
            bins=args.bins
        )

        results[case] = (r, rdf_avg)
        frame_counts[case] = nframes

        # caseごとの全ペアRDFも保存
        header = "r " + " ".join(pair_labels[:rdf_avg.shape[1]])
        out_dat = out_dir / f"{args.prefix}{case}_rdf_pair.dat"
        np.savetxt(out_dat, np.column_stack([r, rdf_avg]), header=header)
        print(f"Saved: {out_dat}")

    # ペアごとに 4, 4-6, 6 を重ね描き
    n_pairs = min(len(pair_labels), next(iter(results.values()))[1].shape[1])

    for pair_idx in range(n_pairs):
        pair_label = pair_labels[pair_idx]

        plt.figure(figsize=(6.4, 4.8))

        combined = None
        columns = []

        for case in args.paths:
            r, rdf_avg = results[case]
            y = rdf_avg[:, pair_idx]

            plt.plot(r, y, label=case)

            if combined is None:
                combined = [r]
                columns = ["r"]

            combined.append(y)
            columns.append(case)

        plt.xlabel("r (Å)")
        plt.ylabel("g(r)")
        plt.title(f"Partial RDF: {pair_label}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        safe_pair_label = pair_label.replace("-", "_")
        out_png = out_dir / f"{args.prefix}compare_{safe_pair_label}.png"
        out_dat = out_dir / f"{args.prefix}compare_{safe_pair_label}.dat"

        plt.savefig(out_png, dpi=300)
        plt.close()

        np.savetxt(
            out_dat,
            np.column_stack(combined),
            header=" ".join(columns)
        )

        print(f"Saved: {out_png}")
        print(f"Saved: {out_dat}")

    # 全ペアを1枚にまとめた確認用プロットも出す
    for case in args.paths:
        r, rdf_avg = results[case]

        plt.figure(figsize=(6.4, 4.8))
        for i in range(n_pairs):
            plt.plot(r, rdf_avg[:, i], label=pair_labels[i])

        plt.xlabel("r (Å)")
        plt.ylabel("g(r)")
        plt.title(f"Partial RDF: {case}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        out_png = out_dir / f"{args.prefix}{case}_rdf_pair.png"
        plt.savefig(out_png, dpi=300)
        plt.close()

        print(f"Saved: {out_png}")

    print("\nFrame counts:")
    for case, nframes in frame_counts.items():
        print(f"  {case}: {nframes} frames")


if __name__ == "__main__":
    main()