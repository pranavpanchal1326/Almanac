# ADR 0000: Python 3.12 under uv; PyTorch built for CUDA 13.0

Date: 2026-11-15        Status: accepted

## Context

The laptop's system Python is 3.14.3. The blueprint asks that the Python version be decided by
installing every core dependency (task 0.1). The GPU is an RTX 5060 Laptop (8 GiB, driver 595.95),
which needs a PyTorch build for CUDA 12.8 or newer.

## Decision

- Python 3.12, installed and pinned by uv (`.python-version`). `requires-python` is `>=3.12,<3.14`.
- Dependencies are locked in `uv.lock`. PyTorch is an optional extra (`train`) taken from the
  official index `https://download.pytorch.org/whl/cu130`: torch 2.14.1+cu130.
- Data lives outside the repository under `D:\almanac-data`.

## Alternatives considered

- Python 3.14: not tried, because 3.12 installed everything at the first attempt and is the
  version the blueprint's templates target.
- The CUDA 12.8 build: its newest Windows wheel for Python 3.12 is torch 2.11, three releases
  behind the CUDA 13.0 build.

## Consequences

`uv sync` without `--extra train` removes PyTorch from the environment. Run Phase 0 scripts with
plain `uv run`; use `--extra train` once training starts.

## Revisit when

A core dependency drops Python 3.12, or the cloud training image uses a different CUDA version.
