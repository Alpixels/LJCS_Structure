# Simple-fluid RDF and static structure factor dataset

This repository contains tools and documentation for distributing and using a compact HDF5 dataset of radial distribution functions, `g(r)`, and static structure factors, `S(k)`, for a simple fluid at several thermodynamic states.

Each thermodynamic state is identified by a unique `state_id` and is physically defined by:

- `packing`
- `temperature`

The data are distributed as encrypted release archives. The password is shared separately by the maintainer.

---

## 1. What this repository contains

A recommended repository layout is:

```text
simple-fluid-rdf-sk-dataset/
├── README.md
├── requirements.txt
├── processing/
│   ├── make_dataset.py
│   └── make_h5_release.py
├── scripts/
│   ├── h5_dataset_tools.py
│   ├── list_states.py
│   ├── match_gr_sk_by_state.py
│   ├── plot_state.py
│   └── export_state.py
└── release/
    └── simple-fluid-h5-release-v1.0.0.7z
```

The release archive is encrypted and should contain a directory like:

```text
h5_release/
├── simple-fluid-gr-v1.0.0.h5
├── simple-fluid-sk-v1.0.0.h5
├── dataset_manifest.csv
├── README_HDF5.md
├── release_summary.json
└── checksums_sha256.txt
```

The two main data files are:

```text
simple-fluid-gr-v1.0.0.h5   Radial distribution function data, g(r)
simple-fluid-sk-v1.0.0.h5   Static structure factor data, S(k)
```

The file `dataset_manifest.csv` records the mapping between each `state_id`, its thermodynamic state, and the corresponding source files.

---

## 2. Access policy

This dataset is shared only with authorized collaborators.

Authorized collaborators may:

- use the data for internal research and analysis,
- reproduce calculations within the collaboration,
- use the scripts in this repository to inspect, plot, or export states,
- cite or acknowledge the dataset according to the project instructions.

Authorized collaborators may not:

- redistribute the encrypted archive,
- redistribute decrypted HDF5 files,
- share the archive password with unauthorized users,
- remove the manifest, checksums, or attribution information.

The archive password is distributed separately by the maintainer.

---

## 3. Step-by-step usage

### Step 1: Clone or download the repository

Clone the private repository or download it from GitHub.

Example:

```bash
git clone <PRIVATE_REPOSITORY_URL>
cd simple-fluid-rdf-sk-dataset
```

Replace `<PRIVATE_REPOSITORY_URL>` with the actual private repository URL.

### Step 2: Install system dependency for encrypted archives

The release archive is expected to be a `.7z` file encrypted with password protection and encrypted headers.

On Ubuntu or Debian:

```bash
sudo apt update
sudo apt install p7zip-full
```

On macOS with Homebrew:

```bash
brew install p7zip
```

On Windows, install 7-Zip from the official 7-Zip application and use either the graphical interface or the `7z` command if it is available in your terminal.

### Step 3: Extract the encrypted release archive

From the repository root, run:

```bash
7z x release/simple-fluid-h5-release-v1.0.0.7z
```

You will be asked for the password. The password is distributed separately by the maintainer.

After extraction, you should have:

```text
h5_release/
├── simple-fluid-gr-v1.0.0.h5
├── simple-fluid-sk-v1.0.0.h5
├── dataset_manifest.csv
├── README_HDF5.md
├── release_summary.json
└── checksums_sha256.txt
```

### Step 4: Verify file integrity

Run:

```bash
cd h5_release
sha256sum -c checksums_sha256.txt
cd ..
```

Each file should report `OK`.

If any file fails the checksum test, do not use the extracted dataset. Download or extract the archive again.

### Step 5: Create a Python environment

Using `venv`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 4. HDF5 data layout

### 4.1 Radial distribution function file

The file `simple-fluid-gr-v1.0.0.h5` stores `g(r)` in rectangular form because all processed `g(r)` files have the same number of radial points.

Expected layout:

```text
state_id              shape: (n_states,)
packing               shape: (n_states,)
temperature           shape: (n_states,)
reduced_density       shape: (n_states,)
number_particles      shape: (n_states,)
simulation_steps      shape: (n_states,)

r                     shape: (n_states, n_r)
g_r                   shape: (n_states, n_r)

source/rho_dir
source/temp_dir
source/raw_gr_file
source/raw_sk_file
source/raw_metadata_file
processed/source_file
```

In the standard release, `n_r = 600`, because each processed `g(r)` file retains the first 600 numeric data rows.

### 4.2 Static structure factor file

The file `simple-fluid-sk-v1.0.0.h5` stores `S(k)` in native ragged form.

This is intentional. The native wave-vector spacing depends on the simulation box length:

```text
DK = 2*pi/L
```

Since `L` depends on density, different thermodynamic states can have different `DK` values and different numbers of `k` points. The HDF5 file therefore preserves each native `S(k)` curve as originally calculated.

No interpolation, truncation, or `NaN` padding is applied to `S(k)`.

Expected layout:

```text
state_id                 shape: (n_states,)
packing                  shape: (n_states,)
temperature              shape: (n_states,)
reduced_density          shape: (n_states,)
number_particles         shape: (n_states,)
simulation_steps         shape: (n_states,)

native/k_flat            shape: (total_k_points,)
native/s_k_flat          shape: (total_k_points,)
native/start_index       shape: (n_states,)
native/length            shape: (n_states,)
native/dk                shape: (n_states,)
native/dk_median_diff    shape: (n_states,)
native/k_min             shape: (n_states,)
native/k_max             shape: (n_states,)

source/rho_dir
source/temp_dir
source/raw_gr_file
source/raw_sk_file
source/raw_metadata_file
processed/source_file
```

For a state with integer index `i`, the corresponding native `S(k)` curve is reconstructed as:

```python
start = start_index[i]
length = length[i]
stop = start + length

k_i = k_flat[start:stop]
s_k_i = s_k_flat[start:stop]
```

The value `native/dk[i]` is the native wave-vector spacing for that state. In this release, `native/dk[i]` is obtained from the first `k` value in the corresponding `S(k)` file, which is consistent with the original calculation where the output starts at `K = DK`.

The value `native/dk_median_diff[i]` is the median spacing between consecutive `k` points. It is included as a consistency check.

---

## 5. Quick inspection commands

All examples below assume the following paths:

```text
h5_release/simple-fluid-gr-v1.0.0.h5
h5_release/simple-fluid-sk-v1.0.0.h5
```

If your files use different names, pass the correct paths through the command-line options shown below.

### 5.1 List available states

```bash
python scripts/list_states.py \
  --gr h5_release/simple-fluid-gr-v1.0.0.h5 \
  --sk h5_release/simple-fluid-sk-v1.0.0.h5
```

Write the state table to CSV:

```bash
python scripts/list_states.py \
  --gr h5_release/simple-fluid-gr-v1.0.0.h5 \
  --sk h5_release/simple-fluid-sk-v1.0.0.h5 \
  --output matched_states.csv
```

### 5.2 Verify that `g(r)` and `S(k)` states match

```bash
python scripts/match_gr_sk_by_state.py \
  --gr h5_release/simple-fluid-gr-v1.0.0.h5 \
  --sk h5_release/simple-fluid-sk-v1.0.0.h5
```

This checks that both HDF5 files contain the same `state_id`, `packing`, and `temperature` values in the same order.

### 5.3 Plot one state

By state index:

```bash
python scripts/plot_state.py \
  --gr h5_release/simple-fluid-gr-v1.0.0.h5 \
  --sk h5_release/simple-fluid-sk-v1.0.0.h5 \
  --index 0 \
  --output state_0001_plot.png
```

By state ID:

```bash
python scripts/plot_state.py \
  --gr h5_release/simple-fluid-gr-v1.0.0.h5 \
  --sk h5_release/simple-fluid-sk-v1.0.0.h5 \
  --state-id state_0001 \
  --output state_0001_plot.png
```

### 5.4 Export one state to text files

```bash
python scripts/export_state.py \
  --gr h5_release/simple-fluid-gr-v1.0.0.h5 \
  --sk h5_release/simple-fluid-sk-v1.0.0.h5 \
  --state-id state_0001 \
  --output-dir exported_states
```

This creates:

```text
exported_states/state_0001_gr.dat
exported_states/state_0001_sk.dat
exported_states/state_0001_metadata.json
```

---

## 6. Minimal Python loading example

```python
import h5py

# Load all g(r) data.
with h5py.File("h5_release/simple-fluid-gr-v1.0.0.h5", "r") as f:
    state_id = f["state_id"][:].astype(str)
    packing = f["packing"][:]
    temperature = f["temperature"][:]
    r = f["r"][:]
    g_r = f["g_r"][:]

print("Number of states:", len(state_id))
print("g(r) shape:", g_r.shape)

# Load native S(k) for the first state.
with h5py.File("h5_release/simple-fluid-sk-v1.0.0.h5", "r") as f:
    i = 0
    start = f["native/start_index"][i]
    length = f["native/length"][i]
    stop = start + length

    k_i = f["native/k_flat"][start:stop]
    s_k_i = f["native/s_k_flat"][start:stop]
    dk_i = f["native/dk"][i]

print("First S(k) length:", len(k_i))
print("First S(k) DK:", dk_i)
```

---

## 7. Notes for machine learning

The `g(r)` data are stored as a regular rectangular array and can be used directly as fixed-size ML input:

```python
X_gr = g_r
```

The `S(k)` data are stored in native ragged form because each state may have a different native `DK` and a different number of `k` points.

This design avoids unnecessary artifacts:

- no interpolation,
- no truncation,
- no artificial common `k` grid,
- no `NaN` padding.

For ML models requiring fixed-size inputs, collaborators must choose and document an additional representation step, such as:

- using only `g(r)` as the fixed-size input,
- extracting scalar or vector summary features from native `S(k)`,
- using sequence models or architectures that accept variable-length inputs,
- creating a separate derived dataset with a carefully documented interpolation procedure.

The distributed release intentionally preserves the native `S(k)` data without imposing such a representation.

---

