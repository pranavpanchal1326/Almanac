"""Real imagery for visual checks: Sentinel-2 Level-2A from the Earth Search public catalogue.

For each site and year, the least cloudy scene inside the site's month window is warped onto the
site's block grid (10 m, north-up). Saves true colour and the near-infrared band, plus a record
of which scene was used.

Contains modified Copernicus Sentinel data.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT

from almanac.common.constants import BLOCK, CELL_M, YEARS

sys.path.insert(0, str(Path(__file__).parent))
from common import IMAGERY, Site, load_sites

STAC = "https://earth-search.aws.element84.com/v1/search"
ENV = {
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "AWS_NO_SIGN_REQUEST": "YES",
    "GDAL_HTTP_MAX_RETRY": "4",
    "GDAL_HTTP_RETRY_DELAY": "2",
    "GDAL_HTTP_TIMEOUT": "120",
}


def search(site: Site, year: int, limit: int = 100) -> list[dict]:
    body = {
        "collections": ["sentinel-2-l2a"],
        "intersects": {"type": "Point", "coordinates": [site.lon, site.lat]},
        "datetime": f"{year}-01-01T00:00:00Z/{year}-12-31T23:59:59Z",
        "limit": limit,
        "query": {"eo:cloud_cover": {"lt": 40}},
    }
    req = urllib.request.Request(
        STAC, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        items = json.load(resp)["features"]
    items = [i for i in items if int(i["properties"]["datetime"][5:7]) in site.imagery_months]
    return sorted(items, key=lambda i: i["properties"]["eo:cloud_cover"])


def warp_to_block(href: str, site: Site, bands: int) -> np.ndarray:
    west, _south, _east, north = site.bounds_utm
    with (
        rasterio.Env(**ENV),
        rasterio.open(href) as src,
        WarpedVRT(
            src,
            crs=CRS.from_epsg(site.tile.epsg),
            transform=from_origin(west, north, CELL_M, CELL_M),
            width=BLOCK,
            height=BLOCK,
            resampling=Resampling.nearest,
        ) as vrt,
    ):
        return vrt.read(list(range(1, bands + 1)))


def fetch(site: Site, year: int) -> dict | None:
    out_dir = IMAGERY / site.name
    out_dir.mkdir(parents=True, exist_ok=True)
    meta_path = out_dir / f"{year}.json"
    if meta_path.exists():
        return json.loads(meta_path.read_text())
    for item in search(site, year)[:6]:
        rgb = warp_to_block(item["assets"]["visual"]["href"], site, 3)
        covered = float((rgb.max(axis=0) > 0).mean())
        if covered < 0.98:
            continue
        nir = warp_to_block(item["assets"]["nir"]["href"], site, 1)[0]
        np.save(out_dir / f"{year}_rgb.npy", rgb)
        np.save(out_dir / f"{year}_nir.npy", nir)
        meta = {
            "site": site.name,
            "year": year,
            "scene": item["id"],
            "datetime": item["properties"]["datetime"],
            "cloud_cover": item["properties"]["eo:cloud_cover"],
            "covered": covered,
        }
        meta_path.write_text(json.dumps(meta, indent=2))
        return meta
    return None


def main() -> None:
    names = set(sys.argv[1:])
    for site in load_sites():
        if names and site.name not in names:
            continue
        years = YEARS if site.role != "orientation" else (2021,)
        for year in years:
            try:
                meta = fetch(site, year)
            except Exception as exc:  # keep going; a missing year is reported, not fatal
                print(f"{site.name} {year}: failed: {exc}", flush=True)
                continue
            print(
                f"{site.name} {year}: {meta['scene'] + ' cloud ' + str(meta['cloud_cover']) if meta else 'no usable scene'}",
                flush=True,
            )


if __name__ == "__main__":
    main()
