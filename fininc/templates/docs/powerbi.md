# Power BI report

A {{n_pbi_pages}}-page report built on a star-schema model with {{n_measures}} DAX measures. It uses the same numbers as the web dashboard and the documents, because all three are generated from the same results.

## Opening it

| File | Use it for |
|---|---|
| [`Pakistan_Financial_Inclusion.pbix`](../powerbi/Pakistan_Financial_Inclusion.pbix) | **Just looking.** The data is inside; double-click and it opens. Needs Power BI Desktop (free from Microsoft). |
| [`Pakistan_Financial_Inclusion.pbip`](../powerbi/Pakistan_Financial_Inclusion.pbip) | **Working on it, or reading it in Git.** A Power BI project: the model is plain text (TMDL) and each page and visual is a small JSON file. A project stores no data, so Power BI Desktop shows a **Refresh now** banner the first time; click it once and wait. |
| [`measures.dax`](../powerbi/measures.dax) | Every measure as text, grouped by folder, with a description. |

`python -m fininc report` regenerates the project and `measures.dax`. The `.pbix` is a snapshot saved from the opened project (File, Save as) and is not rewritten by that command.

## Pages

{{table_pbi_pages}}

Slicers cross-filter the other visuals on a page; the two district slicers work through the relationships below.

## Preview

Every page, saved from Power BI Desktop. Click an image for the full size.

{{pbi_gallery_all}}

## Data model

{{table_pbi_tables}}

```
provinces ──┐
            ├──< districts >──┐
(1 to many) │   (fact table)  │ (1 to many)
district_types ───────────────┘
```

`districts` is the only table with relationships; the others are read by measures that filter them directly (for example `findex[country] = "PAK"`). Each table is stored in the model itself as compressed text, which is how Power BI keeps "Enter data" tables, so the project needs no other file. Columns that hold a district type sort by development rather than alphabetically (`sortByColumn`).

## Measures

{{table_pbi_measures}}

A few patterns worth knowing:

- **Measures live in a table called `_Measures`.** Power BI rejects a table named `Measures`.
- **A year-filtered measure keeps the year in a variable.** Filtering a column by a measure inside `CALCULATE` makes the measure invalid, so the measure first reads the year and then filters by it:

  ```dax
  Pakistan Women % =
  VAR y = [Selected Year]
  RETURN
      CALCULATE ( AVERAGE ( findex[value] ),
                  findex[country] = "PAK", findex[indicator] = "account.t.d.1", findex[year] = y )
  ```

  The same measure works for a card (latest year) and for a line chart (one year per point), because `Selected Year` returns the year on the axis, or the latest when there is none.
- **A disconnected table drives a switch.** The Measure slicer on the District explorer page reads `metric_choice[metric]`, and one measure returns the matching calculation:

  ```dax
  Selected District Metric =
  SWITCH ( SELECTEDVALUE ( metric_choice[metric], "Branches per 100,000 people" ),
           "Branches per 100,000 people", [Branches per 100k],
           "People per branch", [People per Branch],
           ... , BLANK () )
  ```
- **Low density is computed, not stored.** `Districts Below Half National Avg` compares each district with half the national average inside `FILTER`, so it answers to the province and district-type slicers while the national average stays fixed.
- **A rank without `RANKX`.** `Pakistan Rank From Lowest` counts the economies at or below Pakistan's account ownership over `ALL ( countries )`.

## How it was built and checked

- The model, report and theme are written by [`fininc/powerbi`](../fininc/powerbi) from `data/processed`; none of it is edited by hand. The project is written in the format Power BI Desktop itself saves, and its JSON files were checked against Microsoft's published schemas when they were built (Desktop writes a newer visual schema version than the latest one published, so the previous one was used for those files).
- Power BI Desktop was run on the project. All {{n_measures}} measures were evaluated through its local model and had no errors, and their values were compared with the Python results (for example {{branches:,}} branches, {{acct:.1f}}% account ownership, {{units_below_half}} districts below half the national average, and a Gini of {{plan_gini_before:.3f}} before and {{plan_gini_equity:.3f}} after {{k_default:,}} points under the equity rule).
- Every page was opened in Power BI Desktop and inspected, which found and fixed truncated card titles, raw column names and cut-off columns in tables, a scatter chart crowded against the axes and over-long legend labels.

## Limits

- Built and tested with a current Power BI Desktop (the project format needs a recent version). Older versions may not open the `.pbip`; the `.pbix` is saved by the version used here.
- The `.pbix` and the screenshots in [`powerbi_pages`](powerbi_pages) are saved by hand from Power BI Desktop and are not rewritten by `python -m fininc report`. If the data or the generator change, open the project, refresh, check the pages and save them again; a test fails when the `.pbix` no longer matches the report.
- The Global Findex figures are survey estimates; district figures are about branches, not account ownership.
