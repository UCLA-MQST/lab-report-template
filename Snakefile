# Snakefile — Dependency graph for long-running analysis scripts.
#
# Snakemake re-runs a rule only when its input script or data files are
# newer than the declared output.  Add new rules following the pattern below.
#
# Build all outputs:
#   snakemake --cores 1
# Build a single target:
#   snakemake plots/qutip_bell_simulation.png --cores 1

VENV_PY = "venv/bin/python3"


rule all:
    input:
        "plots/qutip_bell_simulation.png",
        "pycode/nb_snippets/auto_nb_code.tex",
        "pycode/nb_snippets/auto_nb_figures.tex",


# ─── QuTiP Bell-state simulation (the main long-running computation) ──────────
rule qutip_bell_simulation:
    input:
        script = "pycode/generate_long_run_plot.py",
        deps   = [
            "pycode/photon_statistics.py",
            "pycode/errors.py",
        ],
    output:
        plot = "plots/qutip_bell_simulation.png",
    log:
        "logs/qutip_bell_simulation.log",
    shell:
        f"{VENV_PY} {{input.script}} {{output.plot}} > {{log}} 2>&1"


# ─── Notebook extraction (optical_simulator.ipynb → auto_nb_*.tex) ────────────
# Produces auto_nb_code.tex (code cells) and auto_nb_figures.tex (figure outputs)
# for use in the report via: \input{auto_nb_code} / \input{auto_nb_figures}
rule extract_notebook:
    input:
        script   = "pycode/nb_to_report.py",
        notebook = "pycode/optical_simulator.ipynb",
    output:
        code    = "pycode/nb_snippets/auto_nb_code.tex",
        figures = "pycode/nb_snippets/auto_nb_figures.tex",
    log:
        "logs/nb_to_report.log",
    shell:
        f"{VENV_PY} {{input.script}} {{input.notebook}} > {{log}} 2>&1"


# ─── Template for additional analysis rules ───────────────────────────────────
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
