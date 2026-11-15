"""The supplier index: one row per file. Queried from a local copy of ``aef_index.parquet``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb

from almanac.common.constants import MIRROR_HTTPS, MIRROR_S3
from almanac.grid.ids import TileRef


@dataclass(frozen=True)
class IndexRow:
    """One file of the supplier's archive."""

    year: int
    url: str
    tile: TileRef


def to_https(path: str) -> str:
    """Index paths are ``s3://us-west-2.opendata.source.coop/...`` (confirmed in task 0.2)."""
    if not path.startswith(MIRROR_S3):
        raise ValueError(f"unexpected index path form: {path!r}")
    return MIRROR_HTTPS + path[len(MIRROR_S3) :]


def files_for_point(index_path: Path, lon: float, lat: float) -> list[IndexRow]:
    """All files, every year, whose footprint box contains a WGS 84 point.

    Footprints of neighbouring UTM zones overlap slightly, so more than one tile can match.
    """
    con = duckdb.connect()
    rows = con.execute(
        """
        SELECT year, path, utm_zone, utm_west, utm_south
        FROM read_parquet(?)
        WHERE wgs84_west <= ? AND wgs84_east >= ? AND wgs84_south <= ? AND wgs84_north >= ?
        ORDER BY utm_zone, utm_west, utm_south, year
        """,
        [str(index_path), lon, lon, lat, lat],
    ).fetchall()
    return [IndexRow(int(y), to_https(p), TileRef(z, int(w), int(s))) for y, p, z, w, s in rows]


def tiles_with_years(
    index_path: Path,
    utm_zone: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> list[tuple[TileRef, dict[int, str]]]:
    """Every tile footprint with the address of its file for each year present, in a fixed order.

    ``bbox`` is (west, south, east, north) in WGS 84; a tile is included when its footprint box
    overlaps it.
    """
    con = duckdb.connect()
    sql = "SELECT utm_zone, utm_west, utm_south, year, path FROM read_parquet(?)"
    params: list[str | float] = [str(index_path)]
    clauses: list[str] = []
    if utm_zone is not None:
        clauses.append("utm_zone = ?")
        params.append(utm_zone)
    if bbox is not None:
        west, south, east, north = bbox
        clauses.append("wgs84_east >= ? AND wgs84_west <= ? AND wgs84_north >= ? AND wgs84_south <= ?")
        params += [west, east, south, north]
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    rows = con.execute(sql + " ORDER BY utm_zone, utm_west, utm_south, year", params).fetchall()
    out: dict[TileRef, dict[int, str]] = {}
    for zone, west_m, south_m, year, path in rows:
        out.setdefault(TileRef(zone, int(west_m), int(south_m)), {})[int(year)] = to_https(path)
    return list(out.items())


def counts_per_year(index_path: Path) -> list[tuple[int, int, int]]:
    """(year, files, UTM zones) for each year."""
    con = duckdb.connect()
    return con.execute(
        "SELECT year, count(*), count(DISTINCT utm_zone) FROM read_parquet(?) GROUP BY year ORDER BY year",
        [str(index_path)],
    ).fetchall()


def counts_per_zone(index_path: Path, year: int) -> list[tuple[str, int]]:
    con = duckdb.connect()
    return con.execute(
        "SELECT utm_zone, count(*) FROM read_parquet(?) WHERE year = ? GROUP BY utm_zone ORDER BY utm_zone",
        [str(index_path), year],
    ).fetchall()


def footprint_summary(index_path: Path) -> dict[str, int]:
    """Distinct footprints, and how many of them have all years present."""
    con = duckdb.connect()
    total, n_years = con.execute(
        "SELECT count(*), count(DISTINCT year) FROM read_parquet(?)", [str(index_path)]
    ).fetchone() or (0, 0)
    footprints, complete = con.execute(
        """
        SELECT count(*), count(*) FILTER (WHERE n = ?)
        FROM (SELECT count(DISTINCT year) AS n FROM read_parquet(?)
              GROUP BY utm_zone, utm_west, utm_south)
        """,
        [n_years, str(index_path)],
    ).fetchone() or (0, 0)
    return {
        "files": int(total),
        "years": int(n_years),
        "footprints": int(footprints),
        "complete_footprints": int(complete),
    }
