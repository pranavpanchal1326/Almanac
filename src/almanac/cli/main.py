"""Command-line entry points. Phase 0 surface: versions, index, fetch block."""

from __future__ import annotations

import hashlib
import importlib
import importlib.metadata as md
import platform
import urllib.request
from pathlib import Path
from typing import Annotated

import numpy as np
import typer

from almanac import __version__
from almanac.common.constants import INDEX_URL, YEARS
from almanac.grid.ids import block_id
from almanac.io import index as index_mod
from almanac.io.reader import TransferLog, read_block

app = typer.Typer(no_args_is_help=True, add_completion=False, help=__doc__)
index_app = typer.Typer(no_args_is_help=True, help="The supplier index.")
fetch_app = typer.Typer(no_args_is_help=True, help="Download data from the supplier.")
app.add_typer(index_app, name="index")
app.add_typer(fetch_app, name="fetch")

DEFAULT_INDEX = Path("D:/almanac-data/index/aef_index.parquet")
IndexOpt = Annotated[Path, typer.Option("--index", help="Local copy of aef_index.parquet.")]


@app.command()
def versions() -> None:
    """Print library versions and the GPU name (acceptance test of task 0.1)."""
    typer.echo(f"almanac {__version__}  python {platform.python_version()}  {platform.platform()}")
    for name in (
        "numpy",
        "rasterio",
        "pyproj",
        "duckdb",
        "zarr",
        "scipy",
        "scikit-learn",
        "pydantic",
        "typer",
        "torch",
    ):
        try:
            typer.echo(f"{name:14s}{md.version(name)}")
        except md.PackageNotFoundError:
            typer.echo(f"{name:14s}not installed")
    import rasterio

    typer.echo(f"{'gdal':14s}{rasterio.__gdal_version__}")
    try:
        torch = importlib.import_module("torch")
    except ImportError:
        typer.echo("gpu           torch not installed (uv sync --extra train)")
        return
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        typer.echo(
            f"{'gpu':14s}{props.name}, {props.total_memory / 2**30:.1f} GiB, CUDA {torch.version.cuda}"
        )
    else:
        typer.echo("gpu           none visible to torch")


@index_app.command("sync")
def index_sync(index: IndexOpt = DEFAULT_INDEX) -> None:
    """Fetch the supplier index and print its digest."""
    index.parent.mkdir(parents=True, exist_ok=True)
    tmp = index.with_suffix(".part")
    with urllib.request.urlopen(INDEX_URL, timeout=120) as resp, tmp.open("wb") as out:
        while chunk := resp.read(1 << 20):
            out.write(chunk)
    tmp.replace(index)
    digest = hashlib.sha256(index.read_bytes()).hexdigest()
    typer.echo(f"{index}  {index.stat().st_size} bytes  sha256 {digest}")


@index_app.command("counts")
def index_counts(index: IndexOpt = DEFAULT_INDEX) -> None:
    """Files per year, and footprint totals."""
    for year, files, zones in index_mod.counts_per_year(index):
        typer.echo(f"{year}  {files:6d} files  {zones} zones")
    typer.echo(str(index_mod.footprint_summary(index)))


@index_app.command("query")
def index_query(lon: float, lat: float, index: IndexOpt = DEFAULT_INDEX) -> None:
    """List the files, for every year, whose footprint box contains a point."""
    for row in index_mod.files_for_point(index, lon, lat):
        typer.echo(f"{row.year}  {row.tile.tile_id}  {row.url}")


@fetch_app.command("block")
def fetch_block(
    lon: float,
    lat: float,
    block_row: Annotated[int, typer.Option(help="Block row, counted from the north, 0..7.")],
    block_col: Annotated[int, typer.Option(help="Block column, 0..7.")],
    out: Annotated[Path, typer.Option(help="Folder for the .npy files.")],
    years: Annotated[str, typer.Option(help="Comma-separated years.")] = ",".join(map(str, YEARS)),
    index: IndexOpt = DEFAULT_INDEX,
) -> None:
    """Download one level-0 block, north-up, for the given years, from the tile containing a point."""
    wanted = {int(y) for y in years.split(",")}
    rows = [r for r in index_mod.files_for_point(index, lon, lat) if r.year in wanted]
    if not rows:
        raise typer.BadParameter("no tile contains that point")
    tile = rows[0].tile
    out.mkdir(parents=True, exist_ok=True)
    for row in (r for r in rows if r.tile == tile):
        with TransferLog() as log:
            values, valid = read_block(row.url, block_row, block_col)
        path = out / f"{block_id(tile, block_row, block_col)}_{row.year}.npy"
        np.save(path, values)
        typer.echo(f"{path.name}  {log.bytes / 1e6:.1f} MB transferred  valid {valid.mean():.4f}")


if __name__ == "__main__":
    app()
