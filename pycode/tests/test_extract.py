"""
test_extract.py
===============
Tests for:
  - Module-level helpers: tex_escape, code_float, figure_float
  - SourceExtractor: extract_method (top-level functions, class methods, missing)
  - Backward-compat shim: extract_method() module function
"""

import textwrap
import tempfile
from pathlib import Path

import pytest
import sys, os

# Ensure pycode/ is importable regardless of CWD
_pycode = Path(__file__).parent.parent
if str(_pycode) not in sys.path:
    sys.path.insert(0, str(_pycode))

from extract import (
    SourceExtractor,
    code_float,
    figure_float,
    tex_escape,
    extract_method,   # backward-compat shim
)


# ---------------------------------------------------------------------------
# Sample Python source shared across tests
# ---------------------------------------------------------------------------

SAMPLE_PY = textwrap.dedent("""\
    def top_func(x):
        \"\"\"A top-level function.\"\"\"
        return x * 2


    class MyClass:
        def method_a(self, y):
            return y + 1

        def method_b(self):
            pass
""")


@pytest.fixture()
def sample_source(tmp_path: Path) -> Path:
    p = tmp_path / "sample.py"
    p.write_text(SAMPLE_PY, encoding="utf-8")
    return p


@pytest.fixture()
def extractor() -> SourceExtractor:
    return SourceExtractor()


# ---------------------------------------------------------------------------
# tex_escape (module-level function and SourceExtractor.tex_escape)
# ---------------------------------------------------------------------------

class TestTexEscape:
    @pytest.mark.parametrize("char,expected", [
        ("&",  r"\&"),
        ("%",  r"\%"),
        ("$",  r"\$"),
        ("#",  r"\#"),
        ("_",  r"\_"),
    ])
    def test_single_special_char(self, char, expected):
        assert tex_escape(char) == expected

    def test_plain_text_unchanged(self):
        assert tex_escape("hello world") == "hello world"

    def test_multiple_specials(self):
        result = tex_escape("R&D: 50% of $100")
        assert r"\&" in result
        assert r"\%" in result
        assert r"\$" in result

    def test_extractor_delegates_to_module(self):
        ex = SourceExtractor()
        assert ex.tex_escape("a_b") == tex_escape("a_b")


# ---------------------------------------------------------------------------
# code_float
# ---------------------------------------------------------------------------

class TestCodeFloat:
    def test_returns_list_of_strings(self):
        result = code_float("pycode/nb_cells/_nb_setup.py", "Setup")
        assert isinstance(result, list)
        assert all(isinstance(s, str) for s in result)

    def test_contains_lstinputlisting(self):
        result = code_float("pycode/nb_cells/_nb_setup.py", "Setup")
        joined = "\n".join(result)
        assert r"\lstinputlisting" in joined
        assert "pycode/nb_cells/_nb_setup.py" in joined

    def test_heading_in_paragraph(self):
        result = code_float("foo.py", "My Heading")
        assert r"\paragraph{My Heading}" in result

    def test_special_chars_escaped_in_heading(self):
        result = code_float("foo.py", "Cost $50 & more")
        joined = "\n".join(result)
        assert r"\$" in joined
        assert r"\&" in joined

    def test_default_placement_H(self):
        result = code_float("foo.py", "X")
        assert r"\begin{Code}[H]" in result

    def test_custom_placement(self):
        result = code_float("foo.py", "X", placement="t")
        assert r"\begin{Code}[t]" in result

    def test_ends_with_empty_string(self):
        result = code_float("foo.py", "X")
        assert result[-1] == ""


# ---------------------------------------------------------------------------
# figure_float
# ---------------------------------------------------------------------------

class TestFigureFloat:
    def test_returns_list_of_strings(self):
        result = figure_float("plot.png", "fig:plot", "My caption.")
        assert isinstance(result, list)

    def test_includegraphics_present(self):
        result = figure_float("my_plot.png", "fig:x", "Cap")
        joined = "\n".join(result)
        assert r"\includegraphics" in joined
        assert "my_plot.png" in joined

    def test_caption_present(self):
        result = figure_float("p.png", "fig:p", r"A \textbf{bold} caption.")
        joined = "\n".join(result)
        assert r"\caption{A \textbf{bold} caption.}" in joined

    def test_label_present(self):
        result = figure_float("p.png", "fig:my-label", "Cap")
        joined = "\n".join(result)
        assert r"\label{fig:my-label}" in joined

    def test_default_width_linewidth(self):
        result = figure_float("p.png", "fig:x", "Cap")
        joined = "\n".join(result)
        assert r"\linewidth" in joined

    def test_custom_width(self):
        result = figure_float("p.png", "fig:x", "Cap", width="0.5\\linewidth")
        joined = "\n".join(result)
        assert "0.5\\linewidth" in joined

    def test_ends_with_empty_string(self):
        result = figure_float("p.png", "fig:x", "Cap")
        assert result[-1] == ""


# ---------------------------------------------------------------------------
# SourceExtractor.extract_method — top-level functions
# ---------------------------------------------------------------------------

class TestExtractTopLevelFunction:
    def test_extracts_function_body(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "top_func", out)
        text = out.read_text()
        assert "def top_func" in text
        assert "return x * 2" in text

    def test_no_leading_whitespace_on_first_line(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "top_func", out)
        first_line = out.read_text().splitlines()[0]
        assert not first_line.startswith(" ")

    def test_ends_with_newline(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "top_func", out)
        assert out.read_text().endswith("\n")

    def test_missing_function_writes_comment(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "nonexistent", out)
        text = out.read_text()
        assert "not found" in text


# ---------------------------------------------------------------------------
# SourceExtractor.extract_method — class methods
# ---------------------------------------------------------------------------

class TestExtractClassMethod:
    def test_extracts_method(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "MyClass.method_a", out)
        text = out.read_text()
        assert "def method_a" in text
        assert "return y + 1" in text

    def test_dedented(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "MyClass.method_a", out)
        assert out.read_text().splitlines()[0].startswith("def ")

    def test_wrong_class_writes_comment(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "NoClass.method_a", out)
        assert "not found" in out.read_text()

    def test_wrong_method_writes_comment(self, extractor, sample_source, tmp_path):
        out = tmp_path / "out.py"
        extractor.extract_method(sample_source, "MyClass.no_method", out)
        assert "not found" in out.read_text()


# ---------------------------------------------------------------------------
# Backward-compatible shim
# ---------------------------------------------------------------------------

class TestBackwardCompatShim:
    def test_shim_works_like_class(self, sample_source, tmp_path):
        out = tmp_path / "shim_out.py"
        extract_method(str(sample_source), "top_func", str(out))
        assert "def top_func" in out.read_text()

    def test_shim_accepts_strings(self, sample_source, tmp_path):
        out = tmp_path / "shim_out2.py"
        # All args as plain strings (as LaTeX calls it)
        extract_method(str(sample_source), "MyClass.method_b", str(out))
        assert "def method_b" in out.read_text()
