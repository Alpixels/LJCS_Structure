#!/usr/bin/env python3
"""Export one thermodynamic state from HDF5 back to text files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from h5_dataset_tools import load_state_pair


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export one state to text files.")
    parser.add_argument("--gr", required=True, type=Path, help="Path to the g(r) HDF5 file.")
    parser.add_argument("--sk", required=True, type=Path, help="Path to the S(k) HDF5 file.")
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--index", type=int, help="Zero-based state index.")
    selector.add_argument("--state-id", help="State identifier, for example state_0001.")
    parser.add_argument("--output-dir", required=True, type=Path, help="Directory where exported files will be written.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    state = load_state_pair(args.gr, args.sk, index=args.index, state_id=args.state_id)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    gr_path = args.output_dir / f"{state.state_id}_gr.dat"
    sk_path = args.output_dir / f"{state.state_id}_sk.dat"
    metadata_path = args.output_dir / f"{state.state_id}_metadata.json"

    gr_header = (
        f"state_id: {state.state_id}\n"
        f"packing: {state.packing:.12g}\n"
        f"temperature: {state.temperature:.12g}\n"
        "columns: r g(r)"
    )
    sk_header = (
        f"state_id: {state.state_id}\n"
        f"packing: {state.packing:.12g}\n"
        f"temperature: {state.temperature:.12g}\n"
        f"dk: {state.dk:.12g}\n"
        "columns: k S(k)"
    )

    np.savetxt(gr_path, np.column_stack([state.r, state.g_r]), header=gr_header)
    np.savetxt(sk_path, np.column_stack([state.k, state.s_k]), header=sk_header)

    metadata = {
        "index": state.index,
        "state_id": state.state_id,
        "packing": state.packing,
        "temperature": state.temperature,
        "reduced_density": state.reduced_density,
        "number_particles": state.number_particles,
        "simulation_steps": state.simulation_steps,
        "gr_rows": int(len(state.r)),
        "sk_rows": int(len(state.k)),
        "sk_dk": state.dk,
        "sk_k_min": float(state.k[0]) if len(state.k) else None,
        "sk_k_max": float(state.k[-1]) if len(state.k) else None,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"Wrote: {gr_path}")
    print(f"Wrote: {sk_path}")
    print(f"Wrote: {metadata_path}")


if __name__ == "__main__":
    main()
