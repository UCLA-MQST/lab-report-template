"""
inline_example.py
-----------------
Example script for pyluatex inline computation.

This file is included verbatim in the report via \\pythoncode{} and also
executed at compile time inside LuaLaTeX via the ``python`` environment.
Keep it short: pyluatex runs this synchronously during compilation.

To produce output in the document, use print() with LaTeX markup:
    print(r"The result is \\textbf{42}.")
"""
import math

phi = math.pi / 4
amplitude = round(math.sin(phi), 3)
print(f"The amplitude at $\\phi = \\pi/4$ is \\textbf{{{amplitude}}}.")
