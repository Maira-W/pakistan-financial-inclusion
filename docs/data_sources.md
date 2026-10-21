# Data sources

Everything in this project comes from public sources. The raw files are stored in [`data/raw`](../data/raw) with a manifest ([`MANIFEST.json`](../data/raw/MANIFEST.json)) that records each file's source URL, licence, size and SHA-256 checksum; `python -m fininc verify` checks that nothing has changed. The 59 files are listed by folder at the end of this page.

## Sources

| Source | What it gives | Vintage | How it is used |
|---|---|---|---|
| **World Bank, Global Findex database** (indicator API, source 28). [Link](https://www.worldbank.org/en/publication/globalfindex) | Account ownership by gender, age, education, income, location and labour status; mobile phone ownership; reasons for having no account; account types and uses | 2011, 2014, 2017, 2021, 2024 | Survey results for Pakistan and for the cross-country benchmark (598 Pakistan and peer observations from 52 indicators; every economy for the benchmark) |
| **World Bank, World Development Indicators** (bulk CSV) | GDP per person, PPP; bank branches and ATMs per 100,000 adults (IMF Financial Access Survey) | to 2024 | Income for the benchmark; an outside check on branch density |
| **State Bank of Pakistan, list of bank and microfinance bank branches** (Excel, sheets *Banks* and *MFBs and DFIs*). [Link](https://www.sbp.org.pk/assets/document/publications/List-of-Banks-and-Microfinance-Banks-Branches_%281%29.xlsx) | 19,115 branches with bank, district, tehsil, rural flag and Islamic flag | 2024-12-31 | Branches by district |
| **State Bank of Pakistan, statistics on scheduled banks, Appendix 3b** (PDF). [Link](https://www.sbp.org.pk/assets/document/IV__Appendices11_statistics_december_2020.pdf) | District-wise bank branches (134 district rows, 14,849 branches) | 2020-12-31 | 2020 baseline for change in branches |
| **State Bank of Pakistan, branchless banking statistics** (9 quarterly PDFs, in the SBP publications folder at `sbp.org.pk/assets/document/publications`) | Mobile wallet accounts, agents, transactions and deposits, nationally and by province, with the split by gender | Apr-Jun 2024 to Apr-Jun 2026 | Digital layer |
| **Pakistan Bureau of Statistics, 7th Population and Housing Census, district tables** (CSV conversion of the PBS Excel tables by [fahad-mirza](https://github.com/fahad-mirza/pakistan_census_2023_tables)) | Tables 01 (population, area, urban and rural, 2017 population), 05 (age), 12 (literacy), 20 (housing), 22 to 25 (lighting, cooking fuel, water, toilets, tenure) | 2023 | Population and development of each district |
| **PBS National Census Report 2023, Table 4.2** | Official provincial totals for 2017 and 2023 | 2023 | Checking only; the PDF is not stored in the repository |
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

| Folder | Files | Bytes | Terms |
| --- | ---: | ---: | --- |
| `data/raw/geo` | 1 | 1,521,807 | CC BY 3.0 IGO (WFP via HDX, redistributed by geoBoundaries) |
| `data/raw/pbs/census2023_district_tables` | 41 | 602,071 | Licence of the CSV conversion repository |
| `data/raw/sbp` | 2 | 2,829,504 | Public statistics of the State Bank of Pakistan |
| `data/raw/sbp/branchless_banking` | 9 | 5,621,495 | Public statistics of the State Bank of Pakistan |
| `data/raw/worldbank` | 6 | 811,231 | CC BY 4.0 (World Bank Open Data) |

## Data problems found, and what was done

1. **A census block counted twice.** In Table 01 the second block for Tando Muhammad Khan (272,427 people, three rows) repeats the first. Version 1 of this project counted it twice. The loader now keeps one row per district and area type, and refuses to continue unless every province matches the official 2023 and 2017 totals exactly.
2. **Missing urban or rural rows.** A district with no urban (or no rural) area has no row for it. Those cells are treated as zero people, and urban plus rural must equal the district total to within 0.5%.
3. **A housing table that carries its own total.** Table 20 has pakka, semi-pakka and kacha rows and a TOTAL row. An early version added all four, halving the pakka share; it is now divided by the TOTAL row, which must equal the household count in Table 22 in every district (it does, exactly).
4. **Detailed tables cover 99.6% of the population.** Age, literacy, housing and service tables leave out some areas (by up to 12% in a district), so ratios are always computed within one table.
5. **Misspellings and a different header.** "Tando Ahyar" for Tando Allahyar; the Islamabad age table names its age column differently.
6. **State Bank spelling and truncation.** 28 district spellings differ between sources ("D.G.Khan", "Bajaur Agency", "Lasbella"). The register cuts "Jaffarabad(Dera Allah Yar)" at 23 characters. All are mapped by an explicit alias table.
7. **A branch filed under the wrong district.** Branches in Gandawah tehsil are listed under Sibi; Gandawah belongs to Jhal Magsi, and is reassigned by tehsil.
8. **Province typed wrongly.** 6 register rows give a province that disagrees with their district (for example a Gujranwala branch typed as Sindh). Branches are assigned by district.
9. **District reorganisations.** Districts created after 2020 are grouped with their parents (see the methodology).
10. **Two districts whose count changes direction.** Musakhel has one bank branch in the 2020 appendix and none in the 2024 register (the only district with no branch), and Jhal Magsi has none in 2020 and one in 2024. Whether that is a closure, a re-coding or an omission cannot be told from the files.
11. **Uncovered regions.** Azad Jammu & Kashmir and Gilgit-Baltistan are absent from the census district tables, so their 793 register branches and 638 2020 branches are set aside.
12. **Wallet statistics out of line.** 3 regional figures jump away from the quarters either side (Balochistan and Gilgit-Baltistan in Oct-Dec 2024, Balochistan's women's share in Jan-Mar 2026). They are flagged and left out of charts, not corrected. Table labels also vary between quarters ("Number of Active Agents"), which the parser handles; the SBP's usual statistics address returns an HTML page, so the same files are downloaded from its publications folder.
13. **Survey labels.** Every Findex indicator label was compared with the World Bank's own name for it. Three of the six reason-for-no-account codes (`fin11d`, `fin11e`, `fin11f`: insufficient funds, someone in the family has an account, lack of trust) were first labelled wrongly; they are fixed and a test pins their meaning. The lack-of-documents reason is published only as a share of all adults and is converted to a share of adults without an account.
14. **Survey error.** The Findex figures are survey estimates with sampling error that the API does not return, so differences of a point or two (for example women's 13.5% in 2021 against 11.9% in 2024) should not be over-read. The direction of the change for women and the poorest is consistent across several groups.
15. **An outside check on branches.** Bank branches per 100,000 adults are 11.8 here for 2024 against 11.2 in the World Bank's indicator (and 10.7 against 10.2 for 2020). The World Bank figure covers the whole country and uses a different adult population, and this project's covers 120 districts, so a small gap is expected.
