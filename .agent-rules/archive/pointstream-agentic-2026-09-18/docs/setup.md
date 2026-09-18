# PointStream Setup and Environment Guide

This guide describes how to configure external data storage, local caching, and dependencies for PointStream.

---

## 1. External Data Storage (`PS_DATA_ROOT`)

PointStream datasets (`assets/`) and run outputs (`outputs/`) hold hundreds of thousands of files. To prevent editor/indexer traversal of large data trees on network filesystems (NFS), **data lives outside the tracked code repository**.

### Precedence Resolution
The runtime path resolver (`src/contracts/paths.py`) resolves `assets/` and `outputs/` using this strict precedence:

1. **Environment Variable**: `PS_DATA_ROOT` (if set and non-empty).
2. **Marker File**: `.ps-data-root` at the repository root. A plain-text, one-line file containing the absolute path to the data root (unquoted). This marker is gitignored and stays local to each checkout or worktree.
3. **Fallback**: The repository root itself (historical default).

### Inspecting Paths
Verify your active data paths with:
```bash
python -c "from src.contracts.paths import describe; print(describe())"
```

### Setting up a Worktree Marker
When creating a new Git worktree, link it to the shared host data directory by creating a `.ps-data-root` file:
```bash
echo "/path/to/shared/pointstream-data" > .ps-data-root
```
> [!WARNING]
> Never create symlinks named `assets` or `outputs` inside the repository tree. File indexers and editors will follow them, defeating the isolation.

---

## 2. Dependencies and Tooling

### Conda Environment
PointStream runs under a pinned Conda environment (typically Python 3.10):
```bash
conda env create -f environment.yaml
conda activate pointstream
```
*Note for shared server installations*: Do not run arbitrary `pip install` commands that can mutate pinned dependencies.

### Native Codec Binaries
Full evaluation requires native video encoders and filters:
- **FFmpeg**: Compiled with `libvmaf`, `libsvtav1`, and `libaom`. Check with:
  ```bash
  ffmpeg -hide_banner -filters | grep libvmaf
  ```
- **VVC Intra**: `vvencapp` / `libvvenc` for VVC background plate encoding:
  ```bash
  command -v vvencapp
  ```
- **OpenCV**: WebP appearance experiments need native WebP image encoding support (`cv2.IMWRITE_WEBP_QUALITY`).

Record resolved executable paths, version/build output, presets, and full command lines for both encoder and decoder. FFmpeg filter availability alone does not establish VVC decoding support; verify a round trip on the actual build. Requirements depend on the selected experiment; synthetic checks do not require every native codec.

---

## 3. Host-Local Caches

On distributed or NFS filesystems, serial file opens for caches impose high latency taxes. Keep all regenerable caches on local host disks (such as `/tmp` or `/var/tmp`), namespaced by checkout:

```bash
PS_CACHE_ROOT="/tmp/pointstream-cache-$USER/$(pwd -P | sha256sum | cut -c1-16)"
mkdir -p "$PS_CACHE_ROOT"
export MYPY_CACHE_DIR="$PS_CACHE_ROOT/mypy"
export RUFF_CACHE_DIR="$PS_CACHE_ROOT/ruff"
export PYTHONPYCACHEPREFIX="$PS_CACHE_ROOT/pycache"
python -m pytest -o "cache_dir=$PS_CACHE_ROOT/pytest" tests/runner/test_tier_end_to_end.py -q
```

Pytest uses the `cache_dir` configuration option; `PYTEST_CACHE_DIR` is not a pytest setting. Pass `-o` on each invocation. The full checkout path hash prevents cache collisions between worktrees with identical basenames. See [pytest configuration](https://docs.pytest.org/en/stable/reference/reference.html#confval-cache_dir).

On this host, import `sqlite3` before `torch` at the package entry point (or in standalone scripts importing Torch). This loads the compatible C++ runtime before Torch pins an older one, avoiding the documented `CXXABI_1.3.15` failure. It is a host workaround, not a reason to add unused imports to every module. The host rules own this requirement.

## 4. Verification

For documentation-only changes, check relative links, referenced commands against their implementation, retired-file recovery entries when changed, and `git diff --check`. CI still runs its configured checks; there is no need to run GPU experiments for prose edits.

For code, configuration, dependency, or executable example changes, run relevant behavior tests and these project checks before merging, in the pinned environment with the cache setup above:

```bash
ruff check .
mypy --config-file pyproject.toml
python -m src.contracts.layers
python -m pytest -o "cache_dir=$PS_CACHE_ROOT/pytest" tests/runner/test_tier_end_to_end.py -q
```

These check lint, static types, dependency direction between layers, and synthetic pipeline integration respectively. They do not establish compression quality or prove a native codec works. Native codec changes also require an encode/decode round trip using the selected binaries. Inspect CI results before merging and report any local checks that could not run.

## 5. Long jobs

Use the [quiet monitoring and bounded adaptation workflow](workflow/long-jobs.md)
for detached runs, report scheduling, codec pilot gates and training selection.
