"""State Bank of Pakistan branch data.

Two sources are read here:
  * the district-wise appendix of "Statistics on Scheduled Banks" at 31 December 2020 (the baseline), and
  * the branch register of banks and microfinance banks at 31 December 2024, one row per branch.
"""

from __future__ import annotations

import pandas as pd
import pdfplumber

from ..paths import RAW

APPENDIX_2020 = RAW / "sbp" / "scheduled_banks_statistics_appendices_2020-12.pdf"
REGISTER_2024 = RAW / "sbp" / "scheduled_banks_and_mfb_branches_2024-12-31.xlsx"


def _to_int(value) -> int | None:
    text = str(value or "").replace(",", "").strip()
    return int(text) if text.isdigit() else None


def load_2020_districts() -> tuple[pd.DataFrame, int]:
    """District-wise scheduled bank branches at 31 Dec 2020, and the grand total printed in the table.

    Each row is checked: conventional + Islamic must equal the total.
    """
    rows, grand_total = [], None
    with pdfplumber.open(APPENDIX_2020) as pdf:
        for page in pdf.pages:
            if "District-Wise Scheduled Banks Branches" not in (page.extract_text() or ""):
                continue
            for table in page.extract_tables():
                for cells in table:
                    if not cells or not cells[0]:
                        continue
                    name = " ".join(str(cells[0]).split())
                    if name.upper() == "DISTRICT":
                        continue
                    conventional, islamic, total = (_to_int(c) for c in cells[1:4])
                    if name.lower() == "grand total":
                        grand_total = total
                        continue
                    rows.append({"sbp_name": name, "conventional": conventional or 0,
                                 "islamic": islamic or 0, "branches": total})
    df = pd.DataFrame(rows)
    bad = df[df["conventional"] + df["islamic"] != df["branches"]]
    if len(bad):
        raise ValueError(f"2020 district rows do not add up:\n{bad}")
    if grand_total is None or int(df["branches"].sum()) != grand_total:
        raise ValueError(f"2020 district rows sum to {df['branches'].sum()} but the table total is {grand_total}")
    return df, grand_total


_COLUMNS = {"Bank": "bank", "Branch Code": "branch_code", "Province": "province_reg", "Division": "division",
            "District": "district_reg", "Tehsil": "tehsil", "City": "city", "Locality": "locality",
            "Area(Rural/Urban)": "area", "Islamic/Conventional": "islamic_flag"}


def load_register() -> pd.DataFrame:
    """Every bank and microfinance/DFI branch at 31 Dec 2024.

    Columns: bank, branch_code, province_reg, division, district_reg, tehsil, city, area (Rural/Urban),
    islamic (bool), rural (bool), kind ("Bank" or "MFB/DFI").
    The province and district fields are as typed in the register; fininc.units resolves them.
    """
    xls = pd.ExcelFile(REGISTER_2024)
    frames = []
    for sheet, kind in (("Banks", "Bank"), ("MFBs and DFIs", "MFB/DFI")):
        title = str(xls.parse(sheet, header=None).iloc[0, 0])
        if "December 31, 2024" not in title:
            raise ValueError(f"Unexpected register date in sheet {sheet!r}: {title!r}")
        df = xls.parse(sheet, header=1)
        df.columns = [str(c).strip() for c in df.columns]
        df = df.rename(columns=_COLUMNS).dropna(how="all")
        for col in ("bank", "province_reg", "division", "district_reg", "tehsil", "city", "area", "islamic_flag"):
            df[col] = df[col].astype("string").str.strip()
        df = df.drop(columns=["locality"])
        df["kind"] = kind
        frames.append(df)
    register = pd.concat(frames, ignore_index=True)

    if not set(register["area"].dropna()) <= {"Rural", "Urban"}:
        raise ValueError("Unexpected values in the Area column")
    if not set(register["islamic_flag"].dropna()) <= {"Islamic", "Conventional"}:
        raise ValueError("Unexpected values in the Islamic/Conventional column")
    register["rural"] = register["area"].eq("Rural")
    register["islamic"] = register["islamic_flag"].eq("Islamic")
    return register.drop(columns=["islamic_flag"])
