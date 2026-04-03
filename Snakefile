# Snakefile — Dependency graph for long-running analysis scripts.
#
# Snakemake re-runs a rule only when its input script or data files are
# newer than the declared output.  Add new rules following the pattern below.
#
# Build all outputs:
#   snakemake --cores 1
# Build a single target:
#   snakemake plots/my_figure.png --cores 1

import os
VENV_PY = os.environ.get("PYTHON", "venv/bin/python3")


rule all:
    input:
        "pycode/nb_snippets/auto_nb_code.tex",
        "pycode/nb_snippets/auto_nb_figures.tex",
        # Add plot targets here as you create analysis scripts:
        # "plots/my_figure.png",


# ─── Notebook extraction (*.ipynb → auto_nb_*.tex) ──────────────────────────
# Produces auto_nb_code.tex (code cells as \nbcellXxx macros)
# and auto_nb_figures.tex (figure outputs) for use in the report via:
#   \input{pycode/nb_snippets/auto_nb_code}
#   \nbcellMyAnalysis   % renders the code cell
NOTEBOOK ?= pycode/analysis.ipynb

rule extract_notebook:
    input:
        script   = "pycode/nb_to_report.py",
        notebook = NOTEBOOK,
    output:
        code    = "pycode/nb_snippets/auto_nb_code.tex",
        figures = "pycode/nb_snippets/auto_nb_figures.tex",
    log:
        "logs/nb_to_report.log",
    shell:
        f"{VENV_PY} {{input.script}} {{input.notebook}} > {{log}} 2>&1"


# ─── Template for analysis rules ─────────────────────────────────────────────
# Uncomment and adapt for each new script:
#
# rule my_analysis:
#     input:
#         script = "pycode/my_analysis_script.py",
#         data   = "data/my_data.csv",
#     output:
#         plot   = "plots/my_figure.png",
#         csv    = "data/my_results.csv",
#     log:
#         "logs/my_analysis.log",
#     shell:
#         f"{VENV_PY} {{input.script}} > {{log}} 2>&1"
