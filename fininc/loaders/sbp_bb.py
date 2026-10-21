"""State Bank of Pakistan quarterly branchless banking (mobile wallet and agent) statistics.

Each quarterly PDF has a national key-indicator table, a province table (accounts, agents, transactions) and,
in most releases, an account table split by gender. The layout moves between releases, so the province table
is read by header position and every quarter is validated: the provinces must add up to the national total.
"""

from __future__ import annotations

import re

import pandas as pd
import pdfplumber

from .. import config
from ..paths import RAW

BB_DIR = RAW / "sbp" / "branchless_banking"
BB_PROVINCES = ["Azad Kashmir", "Balochistan", "Gilgit-Baltistan", "Khyber Pakhtunkhwa",
                "Punjab (Including ISB)", "Sindh"]

_NATIONAL_ROWS = {
    "Number of Agents": "agents",
    "Number of Active BB Ag": "active_agents",
    "Number of Active Agents": "active_agents",   # wording used in the Jul-Sep 2025 release
    "Number of Accounts": "accounts",
    "Number of Active Accou": "active_accounts",
    "Deposits as on Quarter": "deposits_pkr_mn",
}


def _number(text: str) -> float | None:
    cleaned = text.replace(",", "").strip()
    return float(cleaned) if re.fullmatch(r"\d+(\.\d+)?", cleaned) else None


def _row(cells: list) -> list[str]:
    return [" ".join(str(c or "").split()) for c in cells]


def _national(tables: list) -> dict:
    out: dict[str, float] = {}
    for table in tables:
        for cells in map(_row, table):
            for prefix, key in _NATIONAL_ROWS.items():
                if cells and cells[0].startswith(prefix) and key not in out:
                    values = [_number(c) for c in cells[1:] if _number(c) is not None]
                    if values:
                        out[key] = values[0]
    missing = set(_NATIONAL_ROWS.values()) - out.keys()
    if missing:
        raise ValueError(f"Missing national indicators: {sorted(missing)}")
    return out


def _province_table(tables: list) -> pd.DataFrame:
    """Accounts, agents and transactions by province, using the header order to assign columns."""
    for table in tables:
        rows = [_row(r) for r in table]
        header = " ".join(" ".join(r) for r in rows[:3])
        if "Province" not in header or "BB Accounts" not in header or "BB Agents" not in header:
            continue
        order = []
        for r in rows[:2]:
            for cell in r:
                if cell.startswith("BB ") and cell not in order:
                    order.append(cell)
        names = {"BB Accounts": "accounts", "BB Agents": "agents", "BB Transactions": "transactions"}
        out = []
        for cells in rows:
            label = next((c for c in cells if c in BB_PROVINCES), None)
            if label is None:
                continue
            values = [_number(c) for c in cells if _number(c) is not None and not c.endswith("%")]
            if len(values) != len(order):
                raise ValueError(f"Could not read the province row for {label}: {cells}")
            out.append({"province": label, **{names[o]: v for o, v in zip(order, values)}})
        return pd.DataFrame(out)
    raise ValueError("Province table not found")


def _gender_table(tables: list) -> pd.DataFrame | None:
    for table in tables:
        rows = [_row(r) for r in table]
        header = " ".join(" ".join(r) for r in rows[:3])
        if "Male" not in header or "Female" not in header or "Province" not in header:
            continue
        out = []
        for cells in rows:
            label = next((c for c in cells if c in BB_PROVINCES), None)
            if label is None:
                continue
            values = [_number(c) for c in cells if _number(c) is not None and not c.endswith("%")]
            if len(values) >= 3:
                out.append({"province": label, "male": values[0], "female": values[1], "accounts_total": values[2]})
        if out:
            return pd.DataFrame(out)
    return None


def parse_quarter(path) -> tuple[dict, pd.DataFrame]:
    """Return the national indicators and a province table (with the gender split when published)."""
    tables = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables.extend(page.extract_tables())
    national = _national(tables)
    provinces = _province_table(tables)

    for key in ("accounts", "agents"):
        total = provinces[key].sum()
        if abs(total - national[key]) > 0.5:
            raise ValueError(f"{path.name}: provinces sum to {total:,.0f} {key} but the national total is "
                             f"{national[key]:,.0f}")
    gender = _gender_table(tables)
    if gender is not None:
        provinces = provinces.merge(gender[["province", "male", "female"]], on="province", how="left")
        provinces = provinces.rename(columns={"male": "accounts_male", "female": "accounts_female"})
    else:
        provinces["accounts_male"] = float("nan")
        provinces["accounts_female"] = float("nan")
    return national, provinces


def load_all() -> tuple[pd.DataFrame, pd.DataFrame]:
    """National and province tables for every quarter in config.BB_FILES."""
    national_rows, province_frames = [], []
    for quarter in config.BB_FILES:
        national, provinces = parse_quarter(BB_DIR / f"bb_{quarter}.pdf")
        national_rows.append({"quarter": quarter, "label": config.BB_QUARTER_LABELS[quarter], **national})
        province_frames.append(provinces.assign(quarter=quarter, label=config.BB_QUARTER_LABELS[quarter]))
    return pd.DataFrame(national_rows), pd.concat(province_frames, ignore_index=True)
