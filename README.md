# Lab Report Template

This is a comprehensive, reusable directory structure for writing lab reports for MQST-related courses. It utilizes `LuaLaTeX` for advanced macro features and natively tracks short-running and long-running Python analysis pipelines via `Snakemake`, allowing for a Jupyter Notebook-like experience w.r.t. LaTeX type-setting lab reports and enabling single-source-of-truth reproducibility.

---

## Prerequisites (Local Setup)

This section guides a complete beginner through every tool required to build the report locally. Links are provided for further reading and debugging; the summaries below are enough to get started.

---

### 1. Git and GitHub

**What it is:** Git is a version-control system that tracks every change you make to a file. GitHub is a hosting service for Git repositories and adds collaboration features (pull requests, issues) plus CI/CD pipelines (GitHub Actions).

**Install:**
```bash
# macOS (via Homebrew — install Homebrew first from https://brew.sh)
brew install git

# Windows: download from https://git-scm.com/downloads
```

**Essential local workflow:**
```bash
git clone https://github.com/<user>/<repo>   # download a copy
git status                                    # see what changed
git add -p                                    # stage changes interactively
git commit -m "describe what you did"        # save a snapshot
git push                                      # upload to GitHub
git pull                                      # get collaborators' changes
```

**Intermediate techniques:**

| Technique | Command | When to use |
|---|---|---|
| Branches | `git checkout -b my-feature` | Isolate new work from `main` |
| Pull requests | GitHub web UI | Peer review before merging |
| Stashing | `git stash` / `git stash pop` | Save dirty work before pulling |
| Rebasing | `git rebase main` | Keep branch history linear |
| Tags | `git tag v1.0 && git push --tags` | Mark submission snapshots |

**CI/CD and GitHub Actions:** Every push to `main` triggers `.github/workflows/latex.yml`, which automatically: checks out the repo → installs TeX Live and Python → regenerates analysis plots → builds the PDF → uploads it as a build artifact you can download without needing a local TeX install. To view the result, go to the repo on GitHub → **Actions** tab → select the latest run → download the `report` artifact.

**Resources:**
- [Pro Git book (free)](https://git-scm.com/book/en/v2) — comprehensive reference
- [GitHub Skills](https://skills.github.com/) — interactive beginner exercises
- [GitHub Actions docs](https://docs.github.com/en/actions) — workflow syntax reference

---

### 2. LaTeX and LuaLaTeX

**What it is:** LaTeX is a document preparation language. LuaLaTeX is a modern LaTeX engine that can run Lua scripts *inside* the document (used here for CSV parsing macros and the `pyluatex` Python bridge).

**Install:**

| OS | Distribution | Download |
|---|---|---|
| macOS | MacTeX | [tug.org/mactex](https://www.tug.org/mactex/) (~5 GB, includes everything) |
| Linux | TeX Live | `sudo apt install texlive-full` or [tug.org/texlive](https://www.tug.org/texlive/) |
| Windows | MiKTeX | [miktex.org](https://miktex.org/) |

**Verify install:**
```bash
lualatex --version    # should print something like "LuaHBTeX, Version 1.17"
biber --version       # bibliography processor (included in MacTeX)
```

**Key concepts:**
- `--shell-escape` is required because `pyluatex` spawns a Python subprocess during compilation.
- Three-pass build (`lualatex → biber → lualatex`) resolves cross-references and bibliography entries.
- `TMPDIR=/tmp TEXMFVAR=/tmp/texmf-var` are set to avoid macOS/OneDrive path permission issues.

**Resources:**
- [Overleaf LaTeX basics](https://www.overleaf.com/learn/latex/Learn_LaTeX_in_30_minutes) — 30-minute intro
- [LuaLaTeX wiki](https://www.latex-project.org/get/) — engine-specific features
- [pyluatex docs](https://github.com/Diordany/pyluatex) — Python-in-LaTeX bridge

---

### 3. Make and Snakemake

**What Make is:** `make` reads a `Makefile` and runs commands only when their inputs are newer than their outputs — a simple dependency tracker.

**What Snakemake is:** A Python-based workflow manager that extends Make's idea to scientific pipelines. Snakemake knows which analysis scripts produce which plot files and re-runs only the ones whose inputs changed.

**Install:**
```bash
# Snakemake (install into the project venv after activating it)
pip install snakemake

# Make is pre-installed on macOS/Linux; Windows users can get it via
# Git Bash or via Chocolatey: choco install make
```

**Using the Makefile in this repo:**
```bash
make all        # run Snakemake pipeline + compile PDF (full build)
make pdf        # compile PDF only (assumes plots are up-to-date)
make plots      # run Snakemake pipeline only (regenerate analysis outputs)
make clean      # remove LaTeX auxiliary files
make deepclean  # also remove cached plots
```

**Adding a new analysis script:** Add a rule to `Snakefile`:
```python
rule my_analysis:
    input:  "data/raw.csv",
            "pycode/my_script.py"
    output: "plots/my_figure.png"
    shell:  "python3 pycode/my_script.py"
```
Then reference `plots/my_figure.png` in `report.tex` with `\includegraphics`.

**Resources:**
- [GNU Make manual](https://www.gnu.org/software/make/manual/) — complete reference
- [Snakemake tutorial](https://snakemake.readthedocs.io/en/stable/tutorial/tutorial.html) — guided walkthrough

---

### 4. Python via pyenv

**What pyenv is:** A tool that lets you install and switch between multiple Python versions without touching your system Python. Strongly recommended to avoid "works on my machine" version mismatches.

**Install pyenv:**
```bash
# macOS / Linux
curl https://pyenv.run | bash

# Then add to your shell profile (~/.zprofile or ~/.bashrc):
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

**Install a Python version and set it for this project:**
```bash
pyenv install 3.11.9         # install a specific version
pyenv local 3.11.9           # write .python-version file in repo root
python3 --version            # verify: Python 3.11.9
```

**Resources:**
- [pyenv GitHub](https://github.com/pyenv/pyenv) — installation options for all OS
- [Real Python: pyenv guide](https://realpython.com/intro-to-pyenv/) — step-by-step tutorial

---

### 5. Reproducible Python Environment

**Why:** Different versions of `numpy`, `matplotlib`, `scipy` etc. can produce subtly different numerical output or import errors. A `requirements.txt` file pins every package to the exact version used when the report was written.

**One-time setup:**
```bash
# 1. Create a virtual environment (isolated from your system Python)
python3 -m venv venv

# 2. Activate it
source venv/bin/activate          # macOS / Linux
venv\Scripts\activate             # Windows

# 3. Install all dependencies at the pinned versions
pip install -r requirements.txt

# 4. Verify
python3 -c "import numpy, scipy, matplotlib, pandas; print('OK')"
```

You will need to run `source venv/bin/activate` every time you open a new terminal in the project directory. The Makefile and CI pipeline do this automatically.

**Updating or adding packages:**
```bash
pip install <new-package>
pip freeze > requirements.txt    # re-export the full pinned list
git add requirements.txt && git commit -m "add <new-package> dependency"
```

**Resources:**
- [Python venv docs](https://docs.python.org/3/library/venv.html) — official reference
- [pip user guide](https://pip.pypa.io/en/stable/user_guide/) — install, freeze, and manage packages

---

## Directory Structure
| Path | Purpose |
|---|---|
| `data/` | Clean CSVs, BOMs, and raw datasets |
| `pics/` | Static photographs of experimental setups |
| `plots/` | Cached outputs from Snakemake-managed Python scripts |
| `pycode/` | Python scripts, simulations, and unit tests (`pycode/tests/`) |
| `tests/` | Smoke tests for the LaTeX macro environment |

## Tracking & Executing Python Logic

To prevent compiling a heavy document from slowing down due to long parameter sweeps, this template separates computational logic into **Short-Running** and **Long-Running** categories.

### 1. Short-Running Scripts (LaTeX Engine)
Uses the `pyluatex` package embedded directly in `report.tex` (e.g., `\pyc`, `\pysnippetmethod`).
- **Use for**: Quick symbolic math, fast data formatting, computing simple propagation distances.
- **Benefits**: Variables persist directly within the LaTeX environment lifecycle.

### 2. Long-Running Scripts (Snakemake Caching)
Uses `Snakemake` to track data dependencies and cache outputs.
- **Use for**: Heavy plotting, FFT routines, or executing QuTiP Hamiltonian solvers.
- **How it works**: Snakemake compares modification timestamps of `pycode/` scripts vs. generated `plots/` files. **It only re-runs a script if the source or raw data changed.**
- **To add a new long-running script**: Add a rule to `Snakefile` mapping your script to an output in `plots/`, and use `\includegraphics{plots/...}` in `report.tex`.

## How to Build Locally

Ensure you have a modern TeX distribution (`mactex` or `texlive`) installed, alongside `python3`.

```bash
# 1. Create the virtual environment (one-time setup)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Build (triggers snakemake → latexmk automatically)
make all

# 3. Clear cached plots and LaTeX aux files
make deepclean
```

## Configuring VS Code / VSCodium (LaTeX Workshop)

The report uses `LuaLaTeX` with `biber` for bibliography and `--shell-escape` for `pyluatex`. The standard LaTeX Workshop default recipe (`pdflatex`) must be replaced.

### Extension Installation

| IDE | Extension source |
|---|---|
| VS Code | [LaTeX Workshop](https://marketplace.visualstudio.com/items?itemName=James-Yu.latex-workshop) (VS Code Marketplace) |
| VSCodium | Search `James-Yu.latex-workshop` in the **Open VSX Registry** (`https://open-vsx.org`) |

### Settings JSON

Add the following to your **workspace** `.vscode/settings.json` (or user `settings.json`):

```jsonc
{
  // ── LaTeX Workshop: build recipe ──────────────────────────────────────
  "latex-workshop.latex.recipes": [
    {
      "name": "LuaLaTeX + Biber (full)",
      "tools": ["lualatex-shell", "biber", "lualatex-shell", "lualatex-shell"]
    }
  ],

  "latex-workshop.latex.tools": [
    {
      "name": "lualatex-shell",
      "command": "lualatex",
      "args": [
        "--shell-escape",
        "-interaction=nonstopmode",
        "-synctex=1",
        "%DOC%"
      ],
      "env": {
        "TMPDIR": "/tmp",
        "TEXMFVAR": "/tmp/texmf-var"
      }
    },
    {
      "name": "biber",
      "command": "biber",
      "args": ["%DOCFILE%"]
    }
  ],

  // ── Output directory (keep root clean) ────────────────────────────────
  "latex-workshop.latex.outDir": "%DIR%",

  // ── Auto-build on save ─────────────────────────────────────────────────
  "latex-workshop.latex.autoBuild.run": "onSave",

  // ── Forward/inverse SyncTeX (PDF preview) ─────────────────────────────
  "latex-workshop.view.pdf.viewer": "tab",
  "latex-workshop.synctex.afterBuild.enabled": true
}
```

### One-Time Script

Save the following as `configure_latex_workshop.sh` and run it once from the repo root:

```bash
#!/usr/bin/env bash
# Writes .vscode/settings.json for LuaLaTeX + Biber workflow.
set -e
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
  "latex-workshop.latex.recipes": [
    {
      "name": "LuaLaTeX + Biber (full)",
      "tools": ["lualatex-shell", "biber", "lualatex-shell", "lualatex-shell"]
    }
  ],
  "latex-workshop.latex.tools": [
    {
      "name": "lualatex-shell",
      "command": "lualatex",
      "args": ["--shell-escape", "-interaction=nonstopmode", "-synctex=1", "%DOC%"],
      "env": { "TMPDIR": "/tmp", "TEXMFVAR": "/tmp/texmf-var" }
    },
    {
      "name": "biber",
      "command": "biber",
      "args": ["%DOCFILE%"]
    }
  ],
  "latex-workshop.latex.outDir": "%DIR%",
  "latex-workshop.latex.autoBuild.run": "onSave",
  "latex-workshop.view.pdf.viewer": "tab"
}
EOF
echo "Written .vscode/settings.json"
```

> [!NOTE]
> On macOS with OneDrive-synced directories you may also need to set `TMPDIR=/tmp` and `TEXMFVAR=/tmp/texmf-var` in a shell login profile (`.zprofile`) to prevent Biber's Perl runtime from hitting quarantine-locked system temp directories.

### Verifying the Setup

After applying settings, open `lab3/report.tex` → press **Ctrl+Alt+B** (VS Code) or **Ctrl+Shift+B** → select recipe **"LuaLaTeX + Biber (full)"**. The PDF should appear in the side panel within 30–60 seconds.

## Automated GitHub Actions (CI/CD)

The `.github/workflows/latex.yml` pipeline runs on every push to `main`:
1. Provisions an Alpine Linux container with TeX Live and Python 3
2. Restores the `venv` cache via `actions/cache@v4`
3. Runs `snakemake` to regenerate any stale analysis plots
4. Compiles `report.tex` via `lualatex → biber → lualatex × 2`
5. Uploads the final PDF as an Actions Artifact

---

## Notebook Extraction Pipeline

Running `python3 pycode/nb_to_report.py` from the lab directory reads the notebook specified by `NB_PATH` and emits three outputs:

| Output | Purpose |
|---|---|
| `auto_nb_figures.tex` | `\begin{figure}` blocks for each recognized plot; `\input` this in your Results section |
| `auto_nb_code.tex` | `\lstinputlisting` blocks for each code cell; `\input` this in your Analysis Code section |
| `pycode/nb_cells/_nb_*.py` | One snippet file per cell (used by the LaTeX listing above) |
| `pycode/nb_cells/nb_cells.py` | All cells concatenated — runnable standalone for debugging |

**Configure per-lab** by editing three constants at the top of `pycode/nb_to_report.py`:

```python
NB_PATH      = Path("my_analysis.ipynb")   # your notebook
FIGURE_META  = {                            # plot filename → (label, caption)
    "fringe.png": ("fig:fringe", r"Caption text."),
}
WIDTH        = {"fringe.png": "0.75\\linewidth"}  # optional size overrides
```

Then in `report.tex`:

```latex
\input{auto_nb_figures}   % inside \section{Results}
\input{auto_nb_code}      % inside \subsection{Analysis Code}
```

> [!NOTE]
> Snippet files live in `pycode/nb_cells/` (not flat in `pycode/`). The `lstinputlisting` paths in the generated `.tex` files are already correct — no manual adjustment needed.

---

## Uncertainty / Error Analysis Library (`pycode/errors.py`)

All analysis scripts should import from `pycode/errors.py` for consistent error propagation.

```python
from pycode.errors import (
    count_uncertainty,        # sigma_N = sqrt(N)
    rate_uncertainty,         # sigma_R = sqrt(N) / T
    angle_uncertainty,        # readout uncertainty for polariser / waveplate dial
    chi_squared,              # goodness-of-fit dict (chi2, dof, chi2_red, p_value)
    chi_squared_report,       # human-readable string from chi_squared()
    visibility_uncertainty,   # V = (Nmax-Nmin)/(Nmax+Nmin), propagated dV
    E_uncertainty,            # CHSH correlation E(a,b) and Poissonian dE
    accidental_rate,          # R_acc = R_a * R_b * tau_c
)
```

**Angle readout uncertainty** is configurable for any instrument dial:

```python
# Default: quED analyzer (major ticks 10°, minor ticks 5°)
delta = angle_uncertainty(22.5)  # → 0.25°  (between minor ticks)
delta = angle_uncertainty(45.0)  # → 2.5°   (on minor tick)

# Custom instrument with 2° minor ticks:
delta = angle_uncertainty(theta, minor_tick_deg=2.0)
```

---

## CSV-Backed Results Tables (`\csvdatatable`)

Instead of hard-coding numbers, write analysis results to a CSV and read them at compile time:

```latex
\csvdatatable{data/results_fit.csv}%
  {Caption describing the table.}%
  {tab:results-fit}%       % \label
  {lrr}%                   % column spec
  {Quantity \& Value \& $\sigma$ \\\midrule}%   % header row
  {\csvcoli \& \csvcolii \& \csvcoliii}          % data row
```

Any time the Python script updates `data/results_fit.csv`, the next LaTeX build reflects the new values automatically — no manual editing of the `.tex` file required.

---

## Bill of Materials and Component Lists

### BOM CSV format

`data/bom.csv` must have **five columns**:

```
Category, Component, Part Number, Notes / key specs, Lab
```

The fifth column (`Lab`) tags each row for filtering:
- `both` — used in all lab parts
- `3a`, `3b`, etc. — used only in that specific part

### Full BOM table

```latex
\bomtable{data/bom.csv}{List of components.}{tab:bom}
```

Renders as a full-width `table*` with the Notes column wrapped via `tabularx`.

### Filtered component list (for Procedure sections)

```latex
% List all components for lab part 3a (includes "both" + "3a" rows):
\componentlist{3a}{data/bom.csv}

% List shared components only:
\componentlist{both}{data/bom.csv}
```

The `\componentlist` macro uses a Lua function to parse the CSV at compile time, producing a compact `\begin{itemize}` list formatted as:

> **Component name** — Part# *(first note clause)*

This matches the style used in `lab1/report` and `lab2/report`.

> [!TIP]
> When starting a new lab, duplicate the `data/bom.csv` template, fill in your components, and set the `Lab` column appropriately. The component list in the Procedure section will update automatically on the next build.
