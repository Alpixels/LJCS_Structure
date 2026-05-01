#!/usr/bin/env python3
"""Verify that the g(r) and S(k) HDF5 files contain matching states."""

from __future__ import annotations

import argparse
from pathlib import Path

import h5py
import numpy as np

from h5_dataset_tools import _as_str_array, load_state_table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check that g(r) and S(k) HDF5 files match by state.")
    parser.add_argument("--gr", required=True, type=Path, help="Path to the g(r) HDF5 file.")
    parser.add_argument("--sk", required=True, type=Path, help="Path to the S(k) HDF5 file.")
    parser.add_argument("--output", type=Path, help="Optional CSV output path for the matched state table.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with h5py.File(args.gr, "r") as fg, h5py.File(args.sk, "r") as fs:
        gr_state_id = _as_str_array(fg["state_id"])
        sk_state_id = _as_str_array(fs["state_id"])

        if not np.array_equal(gr_state_id, sk_state_id):
            raise SystemExit("ERROR: state_id sequences do not match.")
        if not np.allclose(fg["packing"][:], fs["packing"][:]):
            raise SystemExit("ERROR: packing values do not match.")
        if not np.allclose(fg["temperature"][:], fs["temperature"][:]):
            raise SystemExit("ERROR: temperature values do not match.")

        n_states = len(gr_state_id)
        print(f"OK: g(r) and S(k) files match for {n_states} states.")

    table = load_state_table(args.gr, args.sk)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.output, index=False)
        print(f"Wrote matched state table to: {args.output}")


if __name__ == "__main__":
    main()
