# Data Sources

Status of each source is tracked here. Each download is logged with its date and status.

## 1. World Bank Global Findex

- **Use:** Pakistan's account ownership vs. India, Bangladesh, Sri Lanka; gender gap.
- **Where:** https://www.worldbank.org/en/publication/globalfindex (Data tab). The files were pulled from the World Bank API instead of the full microdata: `https://api.worldbank.org/v2/country/PAK;IND;BGD;LKA/indicator/{indicator}?format=json&date=2011:2024`
- **Indicators:** `FX.OWN.TOTL.ZS` (total account ownership, % age 15+), `FX.OWN.TOTL.FE.ZS` (female), `FX.OWN.TOTL.MA.ZS` (male).
- **Save as:** `data/raw/findex/*.json` (raw API responses, untouched).
- **Tidy output:** `data/clean/findex_account_ownership.csv` (60 rows: country, year, measure, percent).
- **Status:** Downloaded and verified. Years available: 2011, 2014, 2017, 2021, 2024.
- **Pakistan values (% of adults 15+):** Total 10.3 (2011), 13.0 (2014), 21.3 (2017), 21.0 (2021), 27.3 (2024). Female 3.0 → 13.5 (2021) → 11.9 (2024). Male 17.3 → 28.2 (2021) → 42.3 (2024).
- **Note:** The API gives summary indicators, not the full survey microdata. That is enough for the peer benchmark and gender gap, but not for regional analysis within Pakistan.

## 2. Pakistan Bureau of Statistics (PBS), Census 2023

- **Use:** District population for the branches-per-100,000 calculation.
- **Official source:** Population Census 2023 district results, https://census23.pbos.gov.pk/Analysis/DistrictWise (interactive site, checked for Lahore and Islamabad).
- **What was downloaded:** Table 1 (district population) for each province, as converted to CSV by a third party: https://github.com/fahad-mirza/pakistan_census_2023_tables (MIT-style license in the repo). Saved as `data/raw/pbs/census2023_table01_github/*.csv`.
- **Verification:** Islamabad total (2,363,863) and Lahore total (13,004,135) match the official PBS site.
- **Status:** Downloaded and verified against the official site for two districts. The PBS Table 1 PDF URLs I tried returned 404, so the official PDFs were not used.
- **Limits:** Azad Jammu & Kashmir and Gilgit-Baltistan are not in this table, so they are excluded from the analysis.

## 3. State Bank of Pakistan (SBP)

- **Use:** Scheduled bank branches by district.
- **Source:** Statistics on Scheduled Banks in Pakistan, Appendix 3(b), "District-Wise Scheduled Banks Branches as on December 31, 2020": https://www.sbp.org.pk/assets/document/IV__Appendices11_statistics_december_2020.pdf
- **Save as:** `data/raw/sbp/sbp_appendices_dec2020.pdf` (kept untouched).
- **Extraction:** Done with `pdfplumber` in `scripts/build_clean_data.py`. The script checks that conventional + Islamic = total on every row. All 134 rows pass.
- **Status:** Downloaded and extracted. Grand total is 14,849 branches.
- **Data issues found:**
  - The Appendix 2 province table (Dec 2020) does not reconcile with the district table: Islamabad shows 303 in the province table but 558 in the district table. This project uses the district table, which sums to the grand total.
  - The data is from December 2020, while the population is from 2023. This timing gap is stated in the dashboard.
  - AJK and Gilgit-Baltistan rows (15 districts, 638 branches) are excluded because the PBS population table does not cover them.
  - 9 districts that were created after 2020 have no 2020 branch row. They are left blank rather than shown as zero: Chaman, Duki, Jhal Magsi, Sohbatpur, Surab, Sherani, Malakand, Tank, Sujawal.
  - Some 2023 districts were redrawn from older ones, so their 2020 branch counts may not match their 2023 population boundaries.

## Known limitations

- Global Findex is survey-based and measures access and use, not registered accounts.
- SBP branch counts are a supply-side measure; they don't show where people actually bank.
- PBS population figures may be from the 2017 census unless a newer release is available. Note which year you use.
- Source years won't always match. State the year of each data point in the dashboard.
