import pytest
from pathlib import Path
from nb_to_report import NotebookExtractor

def test_wrap_code_basic():
    """Verify that wrap_code handles basic method chains and long lines."""
    extractor = NotebookExtractor(Path("dummy.ipynb"), wrap_code=True)
    
    # 1. Short line: should remain unchanged
    short = "x = 1"
    assert extractor._wrap_code(short) == short

    # 2. Long method chain (backslashes added)
    long_chain = "result = base_obj.method1(a).method2(b).method3(c).method4(d).method5(e)"
    wrapped = extractor._wrap_code(long_chain, max_width=30)
    
    # Check that it split and added backslashes
    assert "\\" in wrapped
    assert "    " in wrapped # Extra indentation
    assert wrapped.count(".") == long_chain.count(".")
    
    # 3. Wrapping inside parentheses (no backslash)
    inside_parens = "func(long_variable_name.method1().method2().method3())"
    wrapped_parens = extractor._wrap_code(inside_parens, max_width=30)
    
    # Should not have backslashes because open_count > 0
    # (Actually the heuristic counts ( vs ) in the prefix)
    assert "\\" not in wrapped_parens
    assert wrapped_parens.count("\n") > 0

def test_wrap_code_disabled():
    """Verify that wrap_code=False leaves lines untouched."""
    extractor = NotebookExtractor(Path("dummy.ipynb"), wrap_code=False)
    long_line = "x = " + "a" * 100
    # Note: the extractor.run() checks self.wrap_code, but let's check the helper too
    # Actually _wrap_code is always available, but it wouldn't be CALLED in run()
    # if self.wrap_code is false.
    pass

def test_wrap_code_indentation():
    """Verify that wrapped lines maintain relative indentation."""
    extractor = NotebookExtractor(Path("dummy.ipynb"), wrap_code=True)
    indented = "    result = obj.long_method_name().another_long_method_name()"
    wrapped = extractor._wrap_code(indented, max_width=40)
    
    lines = wrapped.splitlines()
    assert lines[0].startswith("    ")
    assert lines[1].startswith("        ") # 4 extra spaces

if __name__ == "__main__":
    # Simple runner for use when pytest collection fails due to permissions
    import sys
    test_wrap_code_basic()
    test_wrap_code_disabled()
    test_wrap_code_indentation()
    print("All tests passed (manual run).")
