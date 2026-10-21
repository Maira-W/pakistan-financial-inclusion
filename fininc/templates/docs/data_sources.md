# Data sources

Everything in this project comes from public sources. The raw files are stored in [`data/raw`](../data/raw) with a manifest ([`MANIFEST.json`](../data/raw/MANIFEST.json)) that records each file's source URL, licence, size and SHA-256 checksum; `python -m fininc verify` checks that nothing has changed. The {{n_raw_files}} files are listed by folder at the end of this page.

## Sources

| Source | What it gives | Vintage | How it is used |
|---|---|---|---|
| **World Bank, Global Findex database** (indicator API, source 28). [Link](https://www.worldbank.org/en/publication/globalfindex) | Account ownership by gender, age, education, income, location and labour status; mobile phone ownership; reasons for having no account; account types and uses | 2011, 2014, 2017, 2021, {{findex_year}} | Survey results for Pakistan and for the cross-country benchmark ({{n_findex_rows}} Pakistan and peer observations from {{n_findex_indicators}} indicators; every economy for the benchmark) |
| **World Bank, World Development Indicators** (bulk CSV) | GDP per person, PPP; bank branches and ATMs per 100,000 adults (IMF Financial Access Survey) | to {{findex_year}} | Income for the benchmark; an outside check on branch density |
| **State Bank of Pakistan, list of bank and microfinance bank branches** (Excel, sheets *Banks* and *MFBs and DFIs*). [Link](https://www.sbp.org.pk/assets/document/publications/List-of-Banks-and-Microfinance-Banks-Branches_%281%29.xlsx) | {{register_rows:,}} branches with bank, district, tehsil, rural flag and Islamic flag | {{register_date}} | Branches by district |
| **State Bank of Pakistan, statistics on scheduled banks, Appendix 3b** (PDF). [Link](https://www.sbp.org.pk/assets/document/IV__Appendices11_statistics_december_2020.pdf) | District-wise bank branches ({{sbp20_districts}} district rows, {{sbp20_total:,}} branches) | {{baseline_date}} | 2020 baseline for change in branches |
| **State Bank of Pakistan, branchless banking statistics** ({{wallet_quarters}} quarterly PDFs, in the SBP publications folder at `sbp.org.pk/assets/document/publications`) | Mobile wallet accounts, agents, transactions and deposits, nationally and by province, with the split by gender | {{wallet_first}} to {{wallet_last}} | Digital layer |
| **Pakistan Bureau of Statistics, 7th Population and Housing Census, district tables** (CSV conversion of the PBS Excel tables by [fahad-mirza](https://github.com/fahad-mirza/pakistan_census_2023_tables)) | Tables 01 (population, area, urban and rural, 2017 population), 05 (age), 12 (literacy), 20 (housing), 22 to 25 (lighting, cooking fuel, water, toilets, tenure) | {{census_year}} | Population and development of each district |
| **PBS National Census Report 2023, Table 4.2** | Official provincial totals for 2017 and 2023 | {{census_year}} | Checking only; the PDF is not stored in the repository |
| **geoBoundaries** (gbHumanitarian ADM2 from WFP via HDX). [Link](https://www.geoboundaries.org/) | District polygons | 2022 | Map; polygons are dissolved to the analysis units and simplified |

## Terms of use

| Source | Terms |
|---|---|
| World Bank data | CC BY 4.0 (World Bank Open Data) |
| State Bank of Pakistan files | Public statistics published by the SBP; cite the source |
| Pakistan Bureau of Statistics tables | Public statistics of the PBS; cite the source. The CSV files are a conversion by a third party, kept with that repository's licence file and re-checked here against the official totals |
| geoBoundaries / WFP | CC BY 3.0 IGO |

The code in this repository is the author's own work. This project is independent and is not endorsed by any of these organisations.

## Raw files

{{table_sources}}

## Data problems found, and what was done

1. **A census block counted twice.** In Table 01 the second block for Tando Muhammad Khan (272,427 people, three rows) repeats the first. Version 1 of this project counted it twice. The loader now keeps one row per district and area type, and refuses to continue unless every province matches the official 2023 and 2017 totals exactly.
2. **Missing urban or rural rows.** A district with no urban (or no rural) area has no row for it. Those cells are treated as zero people, and urban plus rural must equal the district total to within 0.5%.
3. **A housing table that carries its own total.** Table 20 has pakka, semi-pakka and kacha rows and a TOTAL row. An early version added all four, halving the pakka share; it is now divided by the TOTAL row, which must equal the household count in Table 22 in every district (it does, exactly).
4. **Detailed tables cover {{detailed_cover:.1f}}% of the population.** Age, literacy, housing and service tables leave out some areas (by up to {{detailed_gap_max:.0f}}% in a district), so ratios are always computed within one table.
5. **Misspellings and a different header.** "Tando Ahyar" for Tando Allahyar; the Islamabad age table names its age column differently.
6. **State Bank spelling and truncation.** {{n_aliases}} district spellings differ between sources ("D.G.Khan", "Bajaur Agency", "Lasbella"). The register cuts "Jaffarabad(Dera Allah Yar)" at 23 characters. All are mapped by an explicit alias table.
7. **A branch filed under the wrong district.** Branches in Gandawah tehsil are listed under Sibi; Gandawah belongs to Jhal Magsi, and is reassigned by tehsil.
8. **Province typed wrongly.** {{register_mismatches}} register rows give a province that disagrees with their district (for example a Gujranwala branch typed as Sindh). Branches are assigned by district.
9. **District reorganisations.** Districts created after 2020 are grouped with their parents (see the methodology).
10. **Two districts whose count changes direction.** Musakhel has one bank branch in the 2020 appendix and none in the 2024 register (the only district with no branch), and Jhal Magsi has none in 2020 and one in 2024. Whether that is a closure, a re-coding or an omission cannot be told from the files.
11. **Uncovered regions.** Azad Jammu & Kashmir and Gilgit-Baltistan are absent from the census district tables, so their {{register_out}} register branches and {{sbp20_out}} 2020 branches are set aside.
12. **Wallet statistics out of line.** {{wallet_flags}} regional figures jump away from the quarters either side (Balochistan and Gilgit-Baltistan in Oct-Dec 2024, Balochistan's women's share in Jan-Mar 2026). They are flagged and left out of charts, not corrected. Table labels also vary between quarters ("Number of Active Agents"), which the parser handles; the SBP's usual statistics address returns an HTML page, so the same files are downloaded from its publications folder.
13. **Survey labels.** Every Findex indicator label was compared with the World Bank's own name for it. Three of the six reason-for-no-account codes (`fin11d`, `fin11e`, `fin11f`: insufficient funds, someone in the family has an account, lack of trust) were first labelled wrongly; they are fixed and a test pins their meaning. The lack-of-documents reason is published only as a share of all adults and is converted to a share of adults without an account.
14. **Survey error.** The Findex figures are survey estimates with sampling error that the API does not return, so differences of a point or two (for example women's {{women_2021:.1f}}% in 2021 against {{women_2024:.1f}}% in 2024) should not be over-read. The direction of the change for women and the poorest is consistent across several groups.
15. **An outside check on branches.** Bank branches per 100,000 adults are {{mine_2024:.1f}} here for {{findex_year}} against {{wdi_2024:.1f}} in the World Bank's indicator (and {{mine_2020:.1f}} against {{wdi_2020:.1f}} for 2020). The World Bank figure covers the whole country and uses a different adult population, and this project's covers {{n_units}} districts, so a small gap is expected.
