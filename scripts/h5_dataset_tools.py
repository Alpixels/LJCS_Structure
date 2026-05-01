#!/usr/bin/env python3
"""
Utilities for reading the simple-fluid HDF5 dataset.

The dataset is distributed as two HDF5 files:

    simple-fluid-gr-v1.0.0.h5
    simple-fluid-sk-v1.0.0.h5

The g(r) file is rectangular:

    r      shape: (n_states, n_r)
    g_r    shape: (n_states, n_r)

The S(k) file is native ragged:

    native/k_flat         shape: (total_k_points,)
    native/s_k_flat       shape: (total_k_points,)
    native/start_index    shape: (n_states,)
    native/length         shape: (n_states,)
    native/dk             shape: (n_states,)

This module centralizes common loading routines used by the command-line
scripts in this repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class StateData:
    """Container for one thermodynamic state.

    Attributes
    ----------
    index:
        Zero-based state index in the HDF5 files.
    state_id:
        Human-readable state identifier, for example ``state_0001``.
    packing:
        Packing fraction defining the thermodynamic state.
    temperature:
        Temperature defining the thermodynamic state.
    r:
        Radial grid for g(r).
    g_r:
        Radial distribution function values.
    k:
        Native wave-vector grid for S(k).
    s_k:
        Static structure factor values on the native k grid.
    dk:
        Native wave-vector spacing for this state.
    reduced_density:
        Reduced density, if present in the file.
    number_particles:
        Number of particles, if present in the file.
    simulation_steps:
        Number of simulation steps, if present in the file.
    """

    index: int
    state_id: str
    packing: float
    temperature: float
    r: np.ndarray
    g_r: np.ndarray
    k: np.ndarray
    s_k: np.ndarray
    dk: float
    reduced_density: float | None = None
    number_particles: int | None = None
    simulation_steps: int | None = None


def _as_str_array(dataset: h5py.Dataset) -> np.ndarray:
    """Read an HDF5 string dataset as a NumPy array of Python strings."""
    data = dataset[:]
    if data.dtype.kind == "S":
        return data.astype(str)
    return np.asarray([x.decode() if isinstance(x, bytes) else str(x) for x in data])


def _optional_float(h5: h5py.File, key: str, index: int) -> float | None:
    if key not in h5:
        return None
    value = float(h5[key][index])
    if np.isnan(value):
        return None
    return value


def _optional_int(h5: h5py.File, key: str, index: int) -> int | None:
    if key not in h5:
        return None
    value = int(h5[key][index])
    if value < 0:
        return None
    return value


def load_state_table(gr_path: str | Path, sk_path: str | Path) -> pd.DataFrame:
    """Load state-level metadata from the g(r) and S(k) HDF5 files.

    Parameters
    ----------
    gr_path:
        Path to the g(r) HDF5 file.
    sk_path:
        Path to the S(k) HDF5 file.

    Returns
    -------
    pandas.DataFrame
        One row per thermodynamic state. Includes state identifiers,
        thermodynamic variables, and S(k) native-grid metadata.
    """
    gr_path = Path(gr_path)
    sk_path = Path(sk_path)

    with h5py.File(gr_path, "r") as fg, h5py.File(sk_path, "r") as fs:
        state_id_gr = _as_str_array(fg["state_id"])
        state_id_sk = _as_str_array(fs["state_id"])

        if not np.array_equal(state_id_gr, state_id_sk):
            raise ValueError("The g(r) and S(k) files do not contain the same state_id sequence.")

        table: dict[str, Any] = {
            "index": np.arange(len(state_id_gr), dtype=int),
            "state_id": state_id_gr,
            "packing": fg["packing"][:],
            "temperature": fg["temperature"][:],
            "sk_length": fs["native/length"][:],
            "sk_dk": fs["native/dk"][:],
            "sk_k_min": fs["native/k_min"][:],
            "sk_k_max": fs["native/k_max"][:],
        }

        if "reduced_density" in fg:
            table["reduced_density"] = fg["reduced_density"][:]
        if "number_particles" in fg:
            table["number_particles"] = fg["number_particles"][:]
        if "simulation_steps" in fg:
            table["simulation_steps"] = fg["simulation_steps"][:]

    return pd.DataFrame(table)


def find_state_index(gr_path: str | Path, *, index: int | None = None, state_id: str | None = None) -> int:
    """Resolve a state index from either an integer index or a state_id.

    Exactly one of ``index`` or ``state_id`` must be provided.
    """
    if (index is None) == (state_id is None):
        raise ValueError("Provide exactly one of index or state_id.")

    with h5py.File(gr_path, "r") as fg:
        n_states = len(fg["state_id"])
        if index is not None:
            if index < 0 or index >= n_states:
                raise IndexError(f"State index {index} is outside valid range [0, {n_states - 1}].")
            return index

        state_ids = _as_str_array(fg["state_id"])
        matches = np.where(state_ids == state_id)[0]
        if len(matches) == 0:
            raise KeyError(f"State ID not found: {state_id}")
        if len(matches) > 1:
            raise ValueError(f"State ID appears more than once: {state_id}")
        return int(matches[0])


def load_state_pair(
    gr_path: str | Path,
    sk_path: str | Path,
    *,
    index: int | None = None,
    state_id: str | None = None,
) -> StateData:
    """Load one matched g(r) and native S(k) state.

    Parameters
    ----------
    gr_path:
        Path to the g(r) HDF5 file.
    sk_path:
        Path to the S(k) HDF5 file.
    index:
        Zero-based state index. Use either ``index`` or ``state_id``.
    state_id:
        State identifier, for example ``state_0001``. Use either ``index`` or
        ``state_id``.

    Returns
    -------
    StateData
        All arrays and metadata for one thermodynamic state.
    """
    gr_path = Path(gr_path)
    sk_path = Path(sk_path)
    i = find_state_index(gr_path, index=index, state_id=state_id)

    with h5py.File(gr_path, "r") as fg, h5py.File(sk_path, "r") as fs:
        gr_state_ids = _as_str_array(fg["state_id"])
        sk_state_ids = _as_str_array(fs["state_id"])

        if not np.array_equal(gr_state_ids, sk_state_ids):
            raise ValueError("The g(r) and S(k) files do not contain matching state_id sequences.")

        start = int(fs["native/start_index"][i])
        length = int(fs["native/length"][i])
        stop = start + length

        return StateData(
            index=i,
            state_id=str(gr_state_ids[i]),
            packing=float(fg["packing"][i]),
            temperature=float(fg["temperature"][i]),
            r=np.asarray(fg["r"][i], dtype=float),
            g_r=np.asarray(fg["g_r"][i], dtype=float),
            k=np.asarray(fs["native/k_flat"][start:stop], dtype=float),
            s_k=np.asarray(fs["native/s_k_flat"][start:stop], dtype=float),
            dk=float(fs["native/dk"][i]),
            reduced_density=_optional_float(fg, "reduced_density", i),
            number_particles=_optional_int(fg, "number_particles", i),
            simulation_steps=_optional_int(fg, "simulation_steps", i),
        )
