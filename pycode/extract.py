"""
extract.py — Python source-code extraction for \\pysnippetmethod.

Provides :class:`SourceExtractor`, which:

  - Extracts a named function or method from a Python source file using
    the ``ast`` module (used by ``\\pysnippetmethod`` in report.tex).
  - Exposes shared LaTeX fragment builders (``code_float``, ``figure_float``,
    ``tex_escape``) that ``NotebookExtractor`` in ``nb_to_report.py`` reuses.

Called automatically by the ``\\pysnippetmethod`` LaTeX macro (via pyluatex):
    \\\\pysnippetmethod[caption]{source.py}{ClassName.method_name}{label}

CLI usage:
    python3 extract.py <source.py> <Class.method|func> <out.py>
"""

from __future__ import annotations

import ast
import textwrap
from pathlib import Path


# ---------------------------------------------------------------------------
# Shared LaTeX helpers (also used by NotebookExtractor in nb_to_report.py)
# ---------------------------------------------------------------------------

def tex_escape(s: str) -> str:
    """Escape special LaTeX characters in a plain-text string."""
    return (
        s.replace("&",  r"\&")
         .replace("%",  r"\%")
         .replace("$",  r"\$")
         .replace("#",  r"\#")
         .replace("_",  r"\_")
    )


def code_float(snippet_rel: str, heading: str, *, placement: str = "H") -> list[str]:
    """
    Return LaTeX lines for a ``Code`` float that includes *snippet_rel* via
    ``\\lstinputlisting``.

    Parameters
    ----------
    snippet_rel:
        Relative path to the ``.py`` snippet file (from the report directory).
    heading:
        Human-readable cell/function heading; will be TeX-escaped.
    placement:
        Float placement specifier (default ``H`` for *here*).
    """
    safe = tex_escape(heading)
    return [
        rf"\paragraph{{{safe}}}",
        rf"\begin{{Code}}[{placement}]",
        rf"  \lstinputlisting[language=Python]{{{snippet_rel}}}",
        rf"  \caption*{{Notebook cell: {safe}}}",
        r"\end{Code}",
        "",
    ]


def figure_float(
    plot_file: str,
    label: str,
    caption: str,
    *,
    width: str = r"\linewidth",
    placement: str = "H",
) -> list[str]:
    """
    Return LaTeX lines for a ``figure`` float including *plot_file*.

    Parameters
    ----------
    plot_file:
        Filename relative to the ``plots/`` directory.
    label:
        LaTeX ``\\label`` key.
    caption:
        Caption string (raw LaTeX, not escaped).
    width:
        ``\\includegraphics`` width (default ``\\linewidth``).
    placement:
        Float placement specifier.
    """
    return [
        rf"\begin{{figure}}[{placement}]",
        r"  \centering",
        rf"  \includegraphics[width={width}]{{plots/{plot_file}}}",
        rf"  \caption{{{caption}}}",
        rf"  \label{{{label}}}",
        r"\end{figure}",
        "",
    ]


# ---------------------------------------------------------------------------
# SourceExtractor — AST-based Python function/method extractor
# ---------------------------------------------------------------------------

class SourceExtractor:
    """
    Extracts named functions or methods from Python source files.

    Instances are lightweight; create one per extraction call or reuse across
    multiple files.

    Example
    -------
    >>> ex = SourceExtractor()
    >>> ex.extract_method("pycode/my_module.py", "MyClass.my_method", "/tmp/out.py")
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_method(
        self,
        source_file: str | Path,
        dotted_name: str,
        out_file: str | Path,
    ) -> None:
        """
        Extract a function or method from *source_file* and write to *out_file*.

        *dotted_name* can be:
          - ``"func_name"``              — top-level function
          - ``"ClassName.method_name"``  — method inside a class

        The indentation of the extracted block is normalized so the first line
        has no leading whitespace.
        """
        snippet = self._extract_snippet(Path(source_file), dotted_name)
        Path(out_file).write_text(snippet, encoding="utf-8")

    # ------------------------------------------------------------------
    # Shared LaTeX helpers (delegated to module-level functions)
    # ------------------------------------------------------------------

    @staticmethod
    def tex_escape(s: str) -> str:
        """Escape special LaTeX characters.  See :func:`tex_escape`."""
        return tex_escape(s)

    @staticmethod
    def code_float(snippet_rel: str, heading: str, **kwargs) -> list[str]:
        """Build a ``Code`` float.  See :func:`code_float`."""
        return code_float(snippet_rel, heading, **kwargs)

    @staticmethod
    def figure_float(plot_file: str, label: str, caption: str, **kwargs) -> list[str]:
        """Build a ``figure`` float.  See :func:`figure_float`."""
        return figure_float(plot_file, label, caption, **kwargs)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _extract_snippet(self, source: Path, dotted_name: str) -> str:
        """Return the dedented source text of the requested node."""
        src = source.read_text(encoding="utf-8")
        tree = ast.parse(src)
        lines = src.splitlines()

        node = self._find_node(tree, dotted_name)
        if node is None:
            return f"# extract.py: '{dotted_name}' not found in {source}\n"

        raw = "\n".join(lines[node.lineno - 1 : node.end_lineno])
        return textwrap.dedent(raw) + "\n"

    @staticmethod
    def _find_node(
        tree: ast.Module,
        dotted_name: str,
    ) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
        """Locate the AST node for *dotted_name* (top-level or Class.method)."""
        parts = dotted_name.split(".")
        _fn_types = (ast.FunctionDef, ast.AsyncFunctionDef)

        if len(parts) == 1:
            for node in ast.walk(tree):
                if isinstance(node, _fn_types) and node.name == parts[0]:
                    return node
        else:
            class_name, method_name = parts[0], parts[1]
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and node.name == class_name:
                    for child in node.body:
                        if isinstance(child, _fn_types) and child.name == method_name:
                            return child
                    break
        return None


# ---------------------------------------------------------------------------
# Module-level shim (backward-compat with \\pysnippetmethod calling
# ``extract.extract_method(file, name, out)`` as a plain function)
# ---------------------------------------------------------------------------

_default_extractor = SourceExtractor()


def extract_method(source_file: str, dotted_name: str, out_file: str) -> None:
    """
    Backward-compatible shim — delegates to :class:`SourceExtractor`.

    Called by the ``\\pysnippetmethod`` LaTeX macro; do NOT rename.
    """
    _default_extractor.extract_method(source_file, dotted_name, out_file)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: extract.py <source.py> <Class.method|func> <out.py>")
        sys.exit(1)
    extract_method(sys.argv[1], sys.argv[2], sys.argv[3])
    print(f"Written to {sys.argv[3]}")
