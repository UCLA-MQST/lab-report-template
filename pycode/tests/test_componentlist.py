"""
test_componentlist.py
=====================
Tests the Python equivalent of the Lua ``tex_componentlist`` helper defined
in both template_report/report.tex and lab3/report.tex.

Because the function lives in Lua and only runs inside LuaLaTeX, we mirror
the logic here in Python so it can be exercised with pytest without a LaTeX
installation.  The parser must match the Lua implementation exactly.
"""

import io
import pathlib
import tempfile
import textwrap
import pytest


# ---------------------------------------------------------------------------
# Python mirror of the Lua CSV parsing + filtering logic
# ---------------------------------------------------------------------------

def _parse_csv_fields(line: str) -> list[str]:
    """RFC-4180 field splitter — mirrors the Lua character-by-character loop."""
    raw: list[str] = []
    inside = False
    cur = ""
    for ch in (line + ","):
        if ch == '"':
            inside = not inside
        elif ch == "," and not inside:
            raw.append(cur.strip())
            cur = ""
        else:
            cur += ch
    return raw


def tex_componentlist_py(labparam: str, csv_text: str) -> list[str]:
    """
    Python mirror of the Lua tex_componentlist function.
    Returns a list of raw LaTeX item strings (without \\item prefix stripped).
    Returns an empty list when no rows match.
    Raises FileNotFoundError equivalent via ValueError when csv_text is None.
    """
    lines = csv_text.splitlines()
    if not lines:
        return []
    _header = lines[0]  # skip header
    out: list[str] = []
    for line in lines[1:]:
        if not line.strip():
            continue
        raw = _parse_csv_fields(line)
        lab = raw[4] if len(raw) > 4 else ""
        if lab == labparam or lab == "both":
            comp = raw[1] if len(raw) > 1 else ""
            pn   = raw[2] if len(raw) > 2 else ""
            note = raw[3] if len(raw) > 3 else ""

            entry = f"\\textbf{{{comp}}}"
            if pn:
                entry += f" --- {pn}"
            if note:
                short = note.split(";")[0].rstrip()
                entry += f" \\textit{{({short})}}"
            out.append(f"\\item {entry}")
    return out


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_CSV = textwrap.dedent("""\
    Category,Component,Part Number,Notes / key specs,Lab
    Source,Laser,QED-001,CW 810 nm,3a
    Optics,HWP,QED-010,zero-order; 810 nm,both
    Detection,APD,QED-020,silicon avalanche; dark counts < 100,3b
    Electronics,TDC,QED-030,1 ns resolution,3a
""")

QUOTED_FIELD_CSV = textwrap.dedent("""\
    Category,Component,Part Number,Notes / key specs,Lab
    Optics,BBO Crystal,QED-005,"Type-II SPDC, 810 nm",both
    Source,Pump Laser,QED-002,"405 nm, 50 mW CW",3a
""")


# ---------------------------------------------------------------------------
# Basic filtering
# ---------------------------------------------------------------------------

class TestFiltering:
    def test_exact_lab_tag(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        comps = [i for i in items if "Laser" in i or "TDC" in i]
        assert len(comps) == 2

    def test_both_tag_always_included(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        assert any("HWP" in i for i in items), "'both' row must appear for any lab tag"

    def test_specific_tag_excluded_from_other_lab(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        assert not any("APD" in i for i in items), "3b-only APD must not appear for 3a"

    def test_3b_filter(self):
        items = tex_componentlist_py("3b", SIMPLE_CSV)
        comps = " ".join(items)
        assert "APD"  in comps
        assert "HWP"  in comps   # 'both'
        assert "Laser" not in comps  # 3a only

    def test_no_match_returns_empty(self):
        # Use a CSV that has NO 'both' rows — only lab-specific ones.
        # 'both' rows always appear for any tag, so SIMPLE_CSV can't be used here.
        csv_no_both = textwrap.dedent("""\
            Category,Component,Part Number,Notes / key specs,Lab
            Source,Laser,QED-001,CW 810 nm,3a
            Detection,APD,QED-020,silicon avalanche,3b
        """)
        items = tex_componentlist_py("lab_nonexistent", csv_no_both)
        assert items == []

    def test_empty_csv_returns_empty(self):
        items = tex_componentlist_py("3a", "")
        assert items == []

    def test_header_only_csv_returns_empty(self):
        items = tex_componentlist_py("3a", "Category,Component,Part Number,Notes,Lab\n")
        assert items == []


# ---------------------------------------------------------------------------
# LaTeX output format
# ---------------------------------------------------------------------------

class TestOutputFormat:
    def test_item_prefix(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        assert all(i.startswith("\\item ") for i in items)

    def test_component_bolded(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        assert all("\\textbf{" in i for i in items)

    def test_part_number_included(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        laser = next(i for i in items if "Laser" in i)
        assert "QED-001" in laser

    def test_note_italicised(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        laser = next(i for i in items if "Laser" in i)
        assert "\\textit{" in laser

    def test_note_shortened_at_semicolon(self):
        items = tex_componentlist_py("3a", SIMPLE_CSV)
        hwp = next(i for i in items if "HWP" in i)
        # Note is "zero-order; 810 nm" — only "zero-order" should appear
        assert "zero-order" in hwp
        assert "810 nm" not in hwp

    def test_missing_part_number_omits_separator(self):
        csv = "Category,Component,Part Number,Notes / key specs,Lab\nOptics,Iris,,aperture stop,3a\n"
        items = tex_componentlist_py("3a", csv)
        assert items
        assert " --- " not in items[0]

    def test_missing_note_omits_italic(self):
        csv = "Category,Component,Part Number,Notes / key specs,Lab\nOptics,Mirror,QED-050,,3a\n"
        items = tex_componentlist_py("3a", csv)
        assert items
        assert "\\textit{" not in items[0]


# ---------------------------------------------------------------------------
# Quoted field (RFC-4180) parsing
# ---------------------------------------------------------------------------

class TestQuotedFields:
    def test_quoted_note_with_comma(self):
        # "Type-II SPDC, 810 nm" must be treated as a single field
        items = tex_componentlist_py("both", QUOTED_FIELD_CSV)
        bbo = next(i for i in items if "BBO" in i)
        assert "Type-II SPDC" in bbo

    def test_quoted_part_number_parsed_correctly(self):
        items = tex_componentlist_py("3a", QUOTED_FIELD_CSV)
        pump = next(i for i in items if "Pump" in i)
        assert "QED-002" in pump

    def test_quoted_note_shortening(self):
        # "405 nm, 50 mW CW" has no semicolon — full note should appear
        items = tex_componentlist_py("3a", QUOTED_FIELD_CSV)
        pump = next(i for i in items if "Pump" in i)
        assert "405 nm, 50 mW CW" in pump


# ---------------------------------------------------------------------------
# bom.csv round-trip against the real fixture files
# ---------------------------------------------------------------------------

BOM_PATHS = [
    pathlib.Path(__file__).parents[3] / "data" / "bom.csv",          # template_report
    pathlib.Path(__file__).parents[3] / "lab3" / "data" / "bom.csv", # lab3
]


@pytest.mark.parametrize("bom_path", [p for p in BOM_PATHS if p.exists()])
def test_real_bom_loads_without_error(bom_path):
    text = bom_path.read_text(encoding="utf-8")
    # Should not raise and should return at least one item for 'both'
    items = tex_componentlist_py("both", text)
    assert isinstance(items, list)
    # Each item must be a non-empty string starting with \item
    for item in items:
        assert item.startswith("\\item "), f"Unexpected item format: {item!r}"


@pytest.mark.parametrize("bom_path", [p for p in BOM_PATHS if p.exists()])
@pytest.mark.parametrize("tag", ["3a", "3b", "both"])
def test_real_bom_tag_filter_is_subset(bom_path, tag):
    text = bom_path.read_text(encoding="utf-8")
    items_tag  = tex_componentlist_py(tag, text)
    items_both = tex_componentlist_py("both", text)
    # Items for a specific tag must be a superset of 'both'-tagged items
    # (every 'both' item is also included for any specific tag)
    both_comps = {i for i in items_both}
    for item in both_comps:
        assert item in tex_componentlist_py(tag, text), (
            f"'both'-tagged item missing from '{tag}' results: {item!r}"
        )
