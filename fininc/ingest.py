"""Download the raw data and record a checksum manifest.

Run once, or again with --refresh:

    python -m fininc ingest

Every later step reads only the files in data/raw/, so the rest of the pipeline works offline.
data/raw/MANIFEST.json lists each file with its source, licence, size and SHA-256 hash, and the
tests check that the files on disk still match it.
"""

from __future__ import annotations

import hashlib
import io
import json
import time
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

from . import config
from .paths import MANIFEST, RAW

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0 Safari/537.36")

LICENCE_WB = "CC BY 4.0 (World Bank Open Data)"
LICENCE_SBP = "Public statistics of the State Bank of Pakistan; cite the source"
LICENCE_PBS = "Public statistics of the Pakistan Bureau of Statistics; cite the source"
LICENCE_GEO = "CC BY 3.0 IGO (WFP via HDX, redistributed by geoBoundaries)"


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------
def _request(url: str, timeout: int = 60, retries: int = 5) -> bytes:
    """GET with retries and exponential backoff. Server errors and timeouts are retried."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            if isinstance(exc, urllib.error.HTTPError) and exc.code < 500 and exc.code != 429:
                break
            time.sleep(min(60, 3 * 2 ** attempt))
    raise RuntimeError(f"Could not download {url}: {last}")


def _json(url: str) -> list | dict:
    return json.loads(_request(url).decode("utf-8"))


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%MZ")


def _load_manifest() -> dict:
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {"files": {}}


def _record(manifest: dict, rel: str, content: bytes, source: str, licence: str, retrieved: str | None) -> None:
    previous = manifest["files"].get(rel, {})
    manifest["files"][rel] = {
        "sha256": hashlib.sha256(content).hexdigest(),
        "bytes": len(content),
        "source": source,
        "licence": licence,
        "retrieved_utc": retrieved or previous.get("retrieved_utc") or _now(),
    }


def _get_file(manifest: dict, rel: str, url: str, licence: str, *, refresh: bool,
              magic: bytes | None = None) -> bool:
    """Download url to data/raw/rel unless it already exists. Returns True when a download happened."""
    path = RAW / rel
    if path.exists() and not refresh:
        _record(manifest, rel, path.read_bytes(), url, licence, None)
        return False
    content = _request(url)
    if magic and not content.startswith(magic):
        raise RuntimeError(f"{url} did not return the expected file type (got {content[:12]!r}). "
                           "The site may be blocking automated downloads.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    _record(manifest, rel, content, url, licence, _now())
    return True


def _get_built(manifest: dict, rel: str, source: str, licence: str, builder: Callable[[], object], *,
               refresh: bool) -> bool:
    """Create a JSON file from several API calls unless it already exists."""
    path = RAW / rel
    if path.exists() and not refresh:
        _record(manifest, rel, path.read_bytes(), source, licence, None)
        return False
    payload = json.dumps(builder(), indent=1, ensure_ascii=False).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    _record(manifest, rel, payload, source, licence, _now())
    return True


# ---------------------------------------------------------------------------
# World Bank
# ---------------------------------------------------------------------------
def _get_wdi_csv(manifest: dict, rel: str, indicator: str, refresh: bool) -> None:
    """Download one WDI indicator for every country as CSV (extracted from the World Bank bulk zip)."""
    url = f"{config.WB_API}/en/indicator/{indicator}?downloadformat=csv"
    path = RAW / rel
    if path.exists() and not refresh:
        _record(manifest, rel, path.read_bytes(), url, LICENCE_WB, None)
        return
    archive = zipfile.ZipFile(io.BytesIO(_request(url)))
    member = next(n for n in archive.namelist() if n.startswith("API_"))
    content = archive.read(member)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    _record(manifest, rel, content, url, LICENCE_WB, _now())


def _wb_rows(url: str) -> list[dict]:
    payload = _json(url)
    if isinstance(payload, list) and len(payload) > 1 and payload[1]:
        return payload[1]
    return []


def _slim(rows: list[dict], with_name: bool = False) -> list[dict]:
    out = []
    for r in rows:
        if r.get("value") is None:
            continue
        item = {"country": r["countryiso3code"] or r["country"]["id"], "year": int(r["date"]), "value": r["value"]}
        if with_name:
            item["name"] = r["country"]["value"]
        out.append(item)
    return out


def fetch_worldbank(manifest: dict, refresh: bool = False) -> None:
    peers = ";".join(config.PEERS)

    def panel() -> dict:
        def one(indicator: str) -> tuple[str, list[dict]]:
            url = f"{config.WB_API}/country/{peers}/indicator/{indicator}?source=28&format=json&date=2011:2025&per_page=500"
            return indicator, _slim(_wb_rows(url))

        with ThreadPoolExecutor(max_workers=4) as pool:
            return dict(pool.map(one, config.FINDEX_CATALOGUE))

    _get_built(manifest, "worldbank/findex_panel_pakistan_and_peers.json",
               f"{config.WB_API}/country/{peers}/indicator/<id>?source=28 (Global Findex)", LICENCE_WB,
               panel, refresh=refresh)

    def world() -> dict:
        def one(indicator: str) -> tuple[str, list[dict]]:
            url = f"{config.WB_API}/country/all/indicator/{indicator}?source=28&format=json&date=2021:2024&per_page=1000"
            return indicator, _slim(_wb_rows(url), with_name=True)

        with ThreadPoolExecutor(max_workers=4) as pool:
            return dict(pool.map(one, config.FINDEX_WORLD_INDICATORS))

    _get_built(manifest, "worldbank/findex_world_2021_2024.json",
               f"{config.WB_API}/country/all/indicator/<id>?source=28 (Global Findex)", LICENCE_WB,
               world, refresh=refresh)

    # WDI series come from the bulk CSV download, which is faster and more reliable than the paged API.
    for indicator, name in (("NY.GDP.PCAP.PP.KD", "gdp_per_capita_ppp"),
                            ("FB.CBK.BRCH.P5", "bank_branches_per_100k_adults"),
                            ("FB.ATM.TOTL.P5", "atms_per_100k_adults")):
        _get_wdi_csv(manifest, f"worldbank/wdi_{name}.csv", indicator, refresh)

    def countries() -> list:
        rows = _json(f"{config.WB_API}/country?format=json&per_page=400")[1]
        return [{"id": c["id"], "name": c["name"], "region": c["region"]["value"],
                 "income": c["incomeLevel"]["value"]} for c in rows]

    _get_built(manifest, "worldbank/countries.json", f"{config.WB_API}/country", LICENCE_WB, countries,
               refresh=refresh)


# ---------------------------------------------------------------------------
# State Bank of Pakistan
# ---------------------------------------------------------------------------
def fetch_sbp(manifest: dict, refresh: bool = False) -> None:
    _get_file(manifest, "sbp/scheduled_banks_and_mfb_branches_2024-12-31.xlsx", config.SBP_BRANCH_REGISTER_URL,
              LICENCE_SBP, refresh=refresh, magic=b"PK")
    _get_file(manifest, "sbp/scheduled_banks_statistics_appendices_2020-12.pdf", config.SBP_APPENDICES_2020_URL,
              LICENCE_SBP, refresh=refresh, magic=b"%PDF")
    for quarter, name in config.BB_FILES.items():
        _get_file(manifest, f"sbp/branchless_banking/bb_{quarter}.pdf", f"{config.SBP_PUBLICATIONS}/{name}",
                  LICENCE_SBP, refresh=refresh, magic=b"%PDF")


# ---------------------------------------------------------------------------
# Pakistan Bureau of Statistics (district tables converted to CSV by a third party)
# ---------------------------------------------------------------------------
def fetch_pbs(manifest: dict, refresh: bool = False) -> None:
    for table in config.CENSUS_TABLES:
        for slug in config.CENSUS_PROVINCE_FILES.values():
            name = f"table_{table}_{slug}_district.csv"
            _get_file(manifest, f"pbs/census2023_district_tables/{name}", f"{config.PBS_TABLES_BASE}/{name}",
                      LICENCE_PBS + " (CSV conversion by fahad-mirza/pakistan_census_2023_tables)",
                      refresh=refresh)
    _get_file(manifest, "pbs/census2023_district_tables/LICENSE_converter_repo.txt",
              "https://raw.githubusercontent.com/fahad-mirza/pakistan_census_2023_tables/main/LICENSE",
              "Licence of the CSV conversion repository", refresh=refresh)

    def official() -> dict:
        return {"source": config.OFFICIAL_CENSUS_SOURCE, "population": config.OFFICIAL_CENSUS_TOTALS}

    _get_built(manifest, "pbs/official_province_totals_2023.json", config.OFFICIAL_CENSUS_SOURCE["url"],
               LICENCE_PBS, official, refresh=refresh)


# ---------------------------------------------------------------------------
# Boundaries
# ---------------------------------------------------------------------------
def fetch_geo(manifest: dict, refresh: bool = False) -> None:
    _get_file(manifest, "geo/pak_adm2_humanitarian_2022_simplified.geojson", config.GEO_URL, LICENCE_GEO,
              refresh=refresh)


STEPS = {"worldbank": fetch_worldbank, "sbp": fetch_sbp, "pbs": fetch_pbs, "geo": fetch_geo}


def run(only: list[str] | None = None, refresh: bool = False) -> dict:
    """Fetch the chosen sources (all by default) and rewrite the manifest."""
    manifest = _load_manifest()
    for name in (only or list(STEPS)):
        print(f"[ingest] {name} ...", flush=True)
        started = time.time()
        STEPS[name](manifest, refresh)
        print(f"[ingest] {name} done in {time.time() - started:.0f}s", flush=True)
    manifest["generated_utc"] = _now()
    manifest["files"] = dict(sorted(manifest["files"].items()))
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    total = sum(f["bytes"] for f in manifest["files"].values())
    print(f"[ingest] manifest lists {len(manifest['files'])} files, {total / 1e6:.1f} MB")
    return manifest


def verify() -> list[str]:
    """Return a list of problems: missing files or files whose hash differs from the manifest."""
    manifest = _load_manifest()
    problems = []
    for rel, info in manifest["files"].items():
        path = RAW / rel
        if not path.exists():
            problems.append(f"missing: {rel}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != info["sha256"]:
            problems.append(f"changed: {rel}")
    return problems
