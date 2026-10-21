"""The documents are generated from templates and the results, so they can be tested like code."""

import re

import pandas as pd
import pytest

from fininc import dictionary, docs, paths
from fininc.text import rank_largest

DOCUMENTS = [paths.ROOT / "README.md", *sorted(paths.DOCS.glob("*.md"))]


def text_of(path):
    return path.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- generated documents
def test_committed_documents_are_what_the_templates_and_data_produce(results):
    for path, expected in docs.render_all(results).items():
        assert text_of(path) == expected, f"{path.name} is out of date: run `python -m fininc report`"


def test_data_dictionary_file_is_current():
    assert text_of(paths.DOCS / "data_dictionary.md") == dictionary.render_markdown()


def test_every_template_value_exists(results):
    values = docs.context(results)
    for template in docs.TEMPLATE_DIR.glob("*.md"):
        for name in docs.PLACEHOLDER.findall(template.read_text(encoding="utf-8")):
            assert name[0] in values, f"{template.name} uses {name[0]}"


def test_every_template_is_used():
    assert {p.name for p in docs.TEMPLATE_DIR.glob("*.md")} == set(docs.OUTPUTS)


def test_a_missing_value_is_an_error_not_a_blank():
    with pytest.raises(KeyError):
        docs.render("{{no_such_value}}", {})
    assert docs.render("{{x:.1f}} points", {"x": 2.345}) == "2.3 points"


def test_ordinals():
    assert [docs.ordinal(n) for n in (1, 2, 3, 4, 6, 11, 12, 21, 22, 101, 112)] == \
        ["1st", "2nd", "3rd", "4th", "6th", "11th", "12th", "21st", "22nd", "101st", "112th"]
    assert docs.largest_phrase(1, 138) == "the largest gap among 138 economies"
    assert docs.largest_phrase(2, 138) == "the 2nd largest gap among 138 economies"
    assert [rank_largest(n) for n in (1, 2, 3, 11)] == ["largest", "2nd largest", "3rd largest", "11th largest"]


# --------------------------------------------------------------------------- quality of the text
def test_no_leftover_placeholders_or_nan():
    for path in DOCUMENTS:
        text = text_of(path)
        assert "{{" not in text and "}}" not in text, path.name
        assert not re.search(r"\bnan\b|\bNaN\b|\binf\b", text), path.name


def test_relative_links_and_images_resolve():
    link = re.compile(r'(?:\]\(|src=")([^)"#\s]+)')
    for path in DOCUMENTS:
        for target in link.findall(text_of(path)):
            if re.match(r"[a-z]+:", target):
                continue
            assert (path.parent / target).exists(), f"{path.name} links to missing {target}"


def test_figures_in_the_readme_exist_and_are_not_empty():
    for name in re.findall(r"docs/figures/([\w.]+\.png)", text_of(paths.ROOT / "README.md")):
        assert (paths.FIGURES / name).stat().st_size > 10_000, name


def test_the_memo_cites_only_computed_numbers_in_its_headline(results):
    memo = text_of(paths.DOCS / "recommendation_memo.md")
    pak = results.summary["cross_country"]["pakistan"]
    assert f"{pak['account']:.0f}%" in memo
    assert f"{results.headline['rural_branch_share']:.0f}%" in memo


def test_no_document_claims_the_wrong_reason_for_having_no_account(results):
    """Three reason codes were once mislabelled; the largest reason is lack of money, and trust is far behind."""
    barriers = results.barriers.set_index("reason")["share_of_unbanked"]
    assert barriers.idxmax() == "Insufficient funds"
    readme = text_of(paths.ROOT / "README.md")
    assert f"{barriers['Insufficient funds']:.0f}% say they do not have enough money" in readme
    for path in DOCUMENTS:
        assert "Religious reasons" not in text_of(path), path.name


# --------------------------------------------------------------------------- the data dictionary
@pytest.mark.parametrize("path", sorted(dictionary.TABLES))
def test_dictionary_describes_every_column_in_order(path):
    file = paths.ROOT / path
    if not file.exists():
        pytest.skip("run `python -m fininc all` first")
    columns = list(pd.read_csv(file, nrows=0).columns)
    described = [c[0] for c in dictionary.TABLES[path]]
    assert columns == described, f"{path}: the dictionary and the file disagree"


def test_every_dictionary_entry_has_a_unit_and_a_meaning():
    for path, rows in dictionary.TABLES.items():
        assert path in dictionary.TITLES
        for name, unit, text in rows:
            assert name and unit and text.endswith(".") and len(text) >= 5, (path, name)
