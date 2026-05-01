#!/usr/bin/env python3
"""Plot g(r) and native S(k) for one thermodynamic state."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt

from h5_dataset_tools import load_state_pair


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot g(r) and native S(k) for one state.")
    parser.add_argument("--gr", required=True, type=Path, help="Path to the g(r) HDF5 file.")
    parser.add_argument("--sk", required=True, type=Path, help="Path to the S(k) HDF5 file.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--index", type=int, help="Zero-based state index.")
    selector.add_argument("--state-id", help="State identifier, for example state_0001.")
    parser.add_argument("--output", type=Path, help="Optional path for saving the figure, for example state_0001.png.")
    parser.add_argument("--show", action="store_true", help="Show the plot interactively after creating it.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = load_state_pair(args.gr, args.sk, index=args.index, state_id=args.state_id)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    axes[0].plot(state.r, state.g_r)
    axes[0].set_xlabel("r")
    axes[0].set_ylabel("g(r)")
    axes[0].set_title("Radial distribution function")

    axes[1].plot(state.k, state.s_k)
    axes[1].set_xlabel("k")
    axes[1].set_ylabel("S(k)")
    axes[1].set_title(f"Static structure factor, DK={state.dk:.6g}")

    fig.suptitle(
        f"{state.state_id}: packing={state.packing:.8g}, T={state.temperature:.8g}",
        y=1.02,
    )
    fig.tight_layout()

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(args.output, dpi=200, bbox_inches="tight")
        print(f"Saved figure to: {args.output}")

    if args.show or not args.output:
        plt.show()


if __name__ == "__main__":
    main()
