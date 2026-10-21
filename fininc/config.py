"""Project constants: data sources, indicator catalogues, colours and model settings.

Nothing here touches the network or the disk, so every module can import it freely.
"""

from __future__ import annotations

SEED = 42

# ---------------------------------------------------------------------------
# Data vintages
# ---------------------------------------------------------------------------
BRANCH_REGISTER_DATE = "2024-12-31"   # SBP register of bank and microfinance branches
BRANCH_BASELINE_DATE = "2020-12-31"   # SBP district-wise appendix used as the 2020 baseline
CENSUS_YEAR = 2023                    # PBS 7th Population and Housing Census
CENSUS_PREVIOUS_YEAR = 2017
FINDEX_YEAR = 2024                    # latest Global Findex round
FINDEX_PREVIOUS_YEAR = 2021

# ---------------------------------------------------------------------------
# Countries
# ---------------------------------------------------------------------------
PEERS = {"PAK": "Pakistan", "IND": "India", "BGD": "Bangladesh", "LKA": "Sri Lanka"}
SOUTH_ASIA = ("AFG", "BGD", "BTN", "IND", "LKA", "MDV", "NPL", "PAK")

# ---------------------------------------------------------------------------
# Global Findex indicators (World Bank source 28). id -> (label, group)
# ---------------------------------------------------------------------------
SEGMENT_INDICATORS = {
    "account.t.d": ("All adults", "overall"),
    "account.t.d.1": ("Women", "gender"),
    "account.t.d.2": ("Men", "gender"),
    "account.t.d.3": ("Young adults (15-24)", "age"),
    "account.t.d.4": ("Older adults (25+)", "age"),
    "account.t.d.5": ("Primary education or less", "education"),
    "account.t.d.6": ("Secondary education or more", "education"),
    "account.t.d.7": ("Poorest 40%", "income"),
    "account.t.d.8": ("Richest 60%", "income"),
    "account.t.d.9": ("Rural", "location"),
    "account.t.d.10": ("Urban", "location"),
    "account.t.d.11": ("Out of the labour force", "labour"),
    "account.t.d.12": ("In the labour force", "labour"),
}

USE_INDICATORS = {
    "fiaccount.t.d": ("Bank or similar institution account", "account_type"),
    "mobileaccount.t.d": ("Mobile money account", "account_type"),
    "dig.acc": ("Digitally enabled account", "account_type"),
    "inactive.t.d": ("Inactive account", "account_type"),
    "fin2.t.d": ("Debit card", "account_type"),
    "fin10": ("Credit card", "account_type"),
    "g20.any": ("Made or received a digital payment", "digital"),
    "g20.made": ("Made a digital payment", "digital"),
    "g20.received": ("Received a digital payment", "digital"),
    "merchant.pay": ("Made a digital merchant payment", "digital"),
    "fin31b": ("Paid a utility bill by mobile phone", "digital"),
    "fin32.acc": ("Received wages into an account", "digital"),
    "fing2p": ("Received government payments", "g2p"),
    "fing2p.acc": ("Government payments received into an account", "g2p"),
    "fing2p.cash": ("Government payments received in cash only", "g2p"),
    "fin17a": ("Saved at a financial institution", "saving"),
    "fin17b": ("Saved using a mobile money account", "saving"),
    "fin17c": ("Saved with a savings club", "saving"),
    "fin22a": ("Borrowed from a formal financial institution", "credit"),
    "fin22b": ("Borrowed from family or friends", "credit"),
    "fin22c": ("Borrowed from a savings club", "credit"),
    "fh1.fh2": ("Sent or received domestic remittances", "remittance"),
    "fh2a": ("Received international remittances", "remittance"),
    "fin28.29": ("Domestic remittances sent or received using an account", "remittance"),
}

MOBILE_INDICATORS = {
    "con1": ("Own a mobile phone", "mobile"),
    "con1.1": ("Own a mobile phone, women", "mobile"),
    "con1.2": ("Own a mobile phone, men", "mobile"),
    "con9a": ("Main phone is a smartphone", "mobile"),
    "con11.s": ("SIM registered in own name (% of phone owners)", "mobile"),
}

# Reasons for not having a bank or similar account, as % of adults without such an account. The labels are the
# World Bank's own wording for each code (checked against the API; a test pins the key words).
BARRIER_INDICATORS = {
    "fin11a.s": ("Financial institutions are too far away", "barrier"),
    "fin11b.s": ("Financial services are too expensive", "barrier"),
    "fin11d.s": ("Insufficient funds", "barrier"),
    "fin11e.s": ("Someone in the family has an account", "barrier"),
    "fin11f.s": ("Lack of trust in financial institutions", "barrier"),
}
# The documentation barrier is only published as a share of all adults; the loader derives the
# share of adults without an account from it. See docs/methodology.md.
DOCUMENTATION_BARRIER = "fin11c"

MOBILE_MONEY_BARRIERS = {
    "fin14a": ("Mobile money agents are too far away", "mm_barrier"),
    "fin14b": ("Mobile money products are too expensive", "mm_barrier"),
    "fin14c": ("Lack of necessary documentation", "mm_barrier"),
    "fin14d": ("Not enough money to use a mobile money account", "mm_barrier"),
}

FINDEX_CATALOGUE: dict[str, tuple[str, str]] = {
    **SEGMENT_INDICATORS, **USE_INDICATORS, **MOBILE_INDICATORS, **BARRIER_INDICATORS,
    DOCUMENTATION_BARRIER: ("Lack of necessary documentation (% of all adults)", "barrier"),
    **MOBILE_MONEY_BARRIERS,
}

# Indicators fetched for every country, for the cross-country benchmark.
FINDEX_WORLD_INDICATORS = (
    "account.t.d", "account.t.d.1", "account.t.d.2",
    "con1", "con1.1", "con1.2",
    "mobileaccount.t.d", "fiaccount.t.d", "g20.any",
)

# ---------------------------------------------------------------------------
# SBP branchless banking quarterly statistics
# ---------------------------------------------------------------------------
BB_FILES = {
    "2024Q2": "Branchless_Banking_Statistics_for_Apr_-_Jun_2024.pdf",
    "2024Q3": "Branchless_Banking_Statistics_for_Jul_-_Sep_2024.pdf",
    "2024Q4": "Branchless-Banking-Statistics-Quarter-Oct-Dec_2024.pdf",
    "2025Q1": "Branchless-Banking-Statistics-Quarter-Jan-Mar_2025.pdf",
    "2025Q2": "Branchless_Banking_Statistics_for_Apr_-_Jun_2025.pdf",
    "2025Q3": "Branchless_Banking_Statistics_for_Jul_to_Sep_2025.pdf",
    "2025Q4": "Branchless_Banking_Statistics_for_Oct_to_Dec_2025.pdf",
    "2026Q1": "Branchless_Banking_Statistics_for_Jan_to_Mar_2026.pdf",
    "2026Q2": "Branchless_Banking_Statistics_for_Apr_to_Jun_2026.pdf",
}
BB_QUARTER_LABELS = {
    "2024Q2": "Apr-Jun 2024", "2024Q3": "Jul-Sep 2024", "2024Q4": "Oct-Dec 2024",
    "2025Q1": "Jan-Mar 2025", "2025Q2": "Apr-Jun 2025", "2025Q3": "Jul-Sep 2025",
    "2025Q4": "Oct-Dec 2025", "2026Q1": "Jan-Mar 2026", "2026Q2": "Apr-Jun 2026",
}

# ---------------------------------------------------------------------------
# Source URLs
# ---------------------------------------------------------------------------
SBP_PUBLICATIONS = "https://www.sbp.org.pk/assets/document/publications"
SBP_BRANCH_REGISTER_URL = f"{SBP_PUBLICATIONS}/List-of-Banks-and-Microfinance-Banks-Branches_%281%29.xlsx"
SBP_APPENDICES_2020_URL = "https://www.sbp.org.pk/assets/document/IV__Appendices11_statistics_december_2020.pdf"
PBS_TABLES_BASE = ("https://raw.githubusercontent.com/fahad-mirza/pakistan_census_2023_tables/main/"
                   "District%20Level%20Tables")
GEO_URL = ("https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbHumanitarian/PAK/ADM2/"
           "geoBoundaries-PAK-ADM2_simplified.geojson")
WB_API = "https://api.worldbank.org/v2"

CENSUS_TABLES = ("01", "05", "12", "20", "22", "23", "24", "25")
CENSUS_PROVINCE_FILES = {
    "Punjab": "punjab", "Sindh": "sindh", "Khyber Pakhtunkhwa": "kp",
    "Balochistan": "balochistan", "Islamabad": "islamabad",
}

# Official totals from the PBS National Census Report 2023, Table 4.2 (page 124).
OFFICIAL_CENSUS_TOTALS = {
    "Pakistan": {"2017": 207_684_626, "2023": 241_499_431},
    "Punjab": {"2017": 109_989_655, "2023": 127_688_922},
    "Sindh": {"2017": 47_854_510, "2023": 55_696_147},
    "Khyber Pakhtunkhwa": {"2017": 35_501_964, "2023": 40_856_097},
    "Balochistan": {"2017": 12_335_129, "2023": 14_894_402},
    "Islamabad": {"2017": 2_003_368, "2023": 2_363_863},
}
OFFICIAL_CENSUS_SOURCE = {
    "document": "PBS National Census Report 2023, Table 4.2: Area, Population Density and Average Household "
                "size by Administrative Units (Census 2023)",
    "url": "https://www.pbs.gov.pk/wp-content/uploads/2020/07/National-Census-Report-2023-2.pdf",
    "note": "Provincial totals are used only to validate the district tables; the PDF is not stored in the repo.",
}

# ---------------------------------------------------------------------------
# Colours (also used by the dashboard and Power BI theme)
# ---------------------------------------------------------------------------
NAVY = "#1F3B57"
TEAL = "#2A9D8F"
ORANGE = "#E76F51"
AMBER = "#E9C46A"
GREY = "#8D99AE"
PURPLE = "#7B2CBF"
PROVINCE_COLOURS = {
    "Punjab": NAVY, "Sindh": TEAL, "Khyber Pakhtunkhwa": ORANGE,
    "Balochistan": AMBER, "Islamabad": PURPLE,
}

# ---------------------------------------------------------------------------
# Model settings
# ---------------------------------------------------------------------------
LOW_DENSITY_SHARE_OF_AVERAGE = 0.5      # "low density" = below half the national branches per 100k
CLUSTER_K_RANGE = (2, 3, 4, 5, 6)
CV_FOLDS = 10
BOOTSTRAP_DRAWS = 500
GAP_SIGNIFICANCE = 0.10                 # probability below which a district has "unusually few" branches
LOW_FEMALE_LITERACY = 40.0              # female literacy (%, age 10+) below which a district counts as low
