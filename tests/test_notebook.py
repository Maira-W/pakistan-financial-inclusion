"""The saved notebook must be the one the code describes, run to the end without errors."""

import json

from fininc import notebook, paths


def load_notebook():
    return json.loads((paths.NOTEBOOKS / "analysis.ipynb").read_text(encoding="utf-8"))


def test_saved_notebook_has_the_cells_the_code_describes():
    saved = load_notebook()["cells"]
    assert len(saved) == len(notebook.CELLS)
    for cell, (kind, source) in zip(saved, notebook.CELLS):
        assert cell["cell_type"] == ("markdown" if kind == notebook.MD else "code")
        assert "".join(cell["source"]) == source


def test_every_code_cell_ran_and_none_failed():
    cells = [c for c in load_notebook()["cells"] if c["cell_type"] == "code"]
    assert cells
    for cell in cells:
        assert cell["execution_count"] is not None
        assert not [o for o in cell["outputs"] if o["output_type"] == "error"]


def test_notebook_checks_itself_against_the_pipeline():
    """The notebook asserts that its own results equal the pipeline's, so a clean run is evidence they agree."""
    assert sum("assert" in source for kind, source in notebook.CELLS if kind == notebook.CODE) >= 8
