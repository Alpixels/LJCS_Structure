#!/usr/bin/env python3
"""List thermodynamic states available in the HDF5 dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

from h5_dataset_tools import load_state_table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="List states in the simple-fluid HDF5 dataset.")
    parser.add_argument("--gr", required=True, type=Path, help="Path to the g(r) HDF5 file.")
    parser.add_argument("--sk", required=True, type=Path, help="Path to the S(k) HDF5 file.")
    parser.add_argument("--output", type=Path, help="Optional CSV output path.")
    parser.add_argument("--max-rows", type=int, default=20, help="Maximum number of rows to print. Default: 20.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    table = load_state_table(args.gr, args.sk)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(args.output, index=False)
        print(f"Wrote state table to: {args.output}")

    columns = ["index", "state_id", "packing", "temperature", "sk_length", "sk_dk", "sk_k_min", "sk_k_max"]
    print(table[columns].head(args.max_rows).to_string(index=False))
    if len(table) > args.max_rows:
        print(f"... showing {args.max_rows} of {len(table)} states. Use --output to save the full table.")
    else:
        print(f"Total states: {len(table)}")


if __name__ == "__main__":
    main()
