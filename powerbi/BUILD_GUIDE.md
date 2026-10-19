# Power BI build guide

This guide builds `Pakistan_Financial_Inclusion.pbix` from the three tables in `powerbi/data/`. It takes about 30–45 minutes the first time. The measures are in `measures.dax` and the colours are in `theme.json`, so you only need to copy and paste.

## 0. Prerequisites

- Power BI Desktop (free, Windows). Install it from the Microsoft Store, or run `winget install Microsoft.PowerBIDesktop`.
- The data tables, which are already in this repo: `powerbi/data/districts.csv`, `provinces.csv`, `findex.csv`.
- If the tables are out of date, rerun `python scripts/build_clean_data.py`, then `python scripts/analysis.py`, then `python scripts/build_powerbi_model.py`.

## 1. Load the data

1. **Home > Get data > Text/CSV.** Pick `powerbi/data/districts.csv`, then **Transform data**.
2. Check the column types in Power Query:
   - `population_2023`, `branches_total`: Whole number
   - `branches_per_100k`, `national_branches_per_100k`: Decimal number
   - `has_branch_data`, `is_combined_unit`, `below_half_national_avg`: True/False
   - `district`, `province`, `province_key`, `status`: Text
3. **Close & Apply.**
4. Repeat for `provinces.csv` (**Get data > Text/CSV**), then for `findex.csv`. In `findex.csv`, set `year` to Whole number and `pct_age_15_plus` to Decimal number.

## 2. Create the relationship

1. Go to the **Model** view.
2. Drag `districts[province_key]` onto `provinces[province_key]`.
3. Cardinality should be **Many to one**, with a single cross-filter direction (from `provinces` to `districts`). Power BI usually sets this automatically.
4. `findex` has no relationship. It is a standalone table, so its visuals filter by country and year only.

## 3. Add the measures

1. In the **Report** view, select `districts` in the Fields pane, then **Home > New table** and enter `Measures = ROW("x", BLANK())`. This creates a home table for the measures. You can hide its `x` column.
2. For each block in `measures.dax`, select the `Measures` table, then **New measure**, paste the block, and press Enter. Power BI shows an error if a name is misspelled.
3. Set formats:
   - `Pakistan Account Ownership %`, `Pakistan Men %`, `Pakistan Women %`, `Gender Gap (pts)`, `India Account Ownership %`: Decimal, 1 decimal place, with a `%` suffix for the percentage measures. For `Gender Gap (pts)`, use a plain number with a " pts" suffix.
   - `Branches per 100k`, `National Branches per 100k`: Decimal, 2 decimal places.
   - `Population Share in Low-Density Districts %`: Percentage, 1 decimal place.
   - `Density vs National (x)`: Decimal, 2 decimal places, with an "x" suffix.

## 4. Apply the theme

**View > Themes > Browse for themes**, then pick `powerbi/theme.json`. This sets the navy, teal and orange colours used in the PNG charts.

## 5. Build the pages

Set each page size to 16:9 (**Format page > Canvas settings**). Use one title text box at the top of each page.

### Page 1: Overview

Title: "Financial Inclusion Gap in Pakistan"

| Visual | Setup |
|---|---|
| 5 card visuals | `Pakistan Account Ownership %`, `Gender Gap (pts)`, `National Branches per 100k`, `Districts Below Half National Avg`, `Population Share in Low-Density Districts %` |
| Line chart: account ownership | X: `findex[year]`. Legend: `findex[country]`. Values: `findex[pct_age_15_plus]`. Visual filter: `findex[measure_label] = All adults`. |
| Clustered bar: branches by province | Y: `provinces[province]`. X: `provinces[branches_per_100k]`. Sort descending. |
| Text box at the bottom | Add a text box, then insert the `Data Note` measure as a field value. Or type the note by hand. |

Slicer: `findex[year]`, placed top right, used by the card visuals. Set it to show the latest year.

### Page 2: Gender

Title: "Men and women: the gap is widening"

| Visual | Setup |
|---|---|
| Line chart: men vs women | X: `findex[year]`. Values: `Pakistan Men %` and `Pakistan Women %`. Visual filter: `findex[country] = Pakistan`. Turn on data labels. |
| Card: gap in selected year | `Gender Gap (pts)` |
| Card: men | `Pakistan Men %` |
| Card: women | `Pakistan Women %` |
| Clustered bar: peers, all adults | X: `findex[pct_age_15_plus]`. Y: `findex[country]`. Visual filter: `findex[measure_label] = All adults`, `findex[year]` = latest. |

### Page 3: District explorer

Title: "Where branches are thin on the ground"

| Visual | Setup |
|---|---|
| Slicer: `districts[province]` | Dropdown or list, top left |
| Slicer: `districts[status]` | Used to hide the nine districts created after 2020 |
| Bar chart: districts | Y: `districts[district]`. X: `districts[branches_per_100k]`. Visual filter: Top N, top 15 by `branches_per_100k`. Set the bar colour to conditional, using the `Bar Colour` measure. |
| Table: all districts | Columns: `district`, `province`, `population_2023`, `branches_total`, `branches_per_100k`, `below_half_national_avg`. Add conditional formatting to `branches_per_100k`. Sort ascending. |
| Card: districts below half | `Districts Below Half National Avg` |
| Card: matched districts | `Districts Matched` |

Turn on **Edit interactions** for the slicers so the bar chart and table respond to them.

### Page 4: About the data

Text boxes covering:

- **Question:** Where are people excluded from formal finance, and how much do gender and geography shape that gap?
- **Sources:** World Bank Global Findex (2011–2024). SBP scheduled bank branches by district, 31 Dec 2020. PBS Population Census 2023, district population.
- **Method:** Branches per 100,000 people, matched districts only. Low density means below half the national average.
- **Limitations:** Branch counts show where banks are, not where people bank, and mobile wallets are not counted. Branch data is from 2020 and population from 2023. AJK and Gilgit-Baltistan are excluded. Nine districts created after 2020 have no branch data.

## 6. Save and export

1. **File > Save as**, to `powerbi/Pakistan_Financial_Inclusion.pbix`.
2. Export a PNG of each page for the README. Use a screenshot tool, and save the files in `dashboard/` as `powerbi_01_overview.png` and so on.
3. To share it online, **Publish > Publish to web** in Power BI. This makes the report public to anyone with the link, so only do it when you're happy for the data and the dashboard to be visible. Put the link in the README.

## Checks before publishing

- The national density shows **5.95** per 100k. It is also in the README and the memo.
- Districts below half the national average shows **39**.
- Population share in low-density districts shows **17.0%**.
- Pakistan account ownership in 2024 shows **27.3%**, with a gender gap of **30.4** points.

If any of these differ, check the relationship in step 2 and the measure definitions in step 3.
