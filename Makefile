.PHONY: all pdf plots notebooks tests clean deepclean

# ─── Venv setup ───────────────────────────────────────────────────────────────
VENV    := venv
PYTHON  := $(VENV)/bin/python3
ACTIVATE := . $(VENV)/bin/activate

# Create venv if Python binary is missing
venv: $(PYTHON)
$(PYTHON):
	python3 -m venv $(VENV)
	$(ACTIVATE) && pip install -q -r requirements.txt

# ─── BOM Validation (Single Source of Truth) ──────────────────────────────────
validate-bom:
	@HEAD=$$(head -n 1 data/bom.csv | tr -d '\r'); \
	EXPECT="Category,Component,Model,Specs,Lab"; \
	if [ "$$HEAD" != "$$EXPECT" ]; then \
	  echo "ERROR: data/bom.csv header mismatch."; \
	  echo "Expected: $$EXPECT"; \
	  echo "Found:    $$HEAD"; \
	  exit 1; \
	fi
	@echo "BOM validation passed."

# ─── Full build: pipeline → notebooks → PDF ───────────────────────────────────
all: validate-bom plots notebooks pdf

# ─── PDF compilation (lualatex → biber → lualatex × 2) ───────────────────────
# TMPDIR/TEXMFVAR prevent Biber hitting permission-restricted system paths.
pdf: venv
	$(ACTIVATE) && \
	  export TMPDIR=/tmp && \
	  export TEXMFVAR=/tmp/texmf-var && \
	  lualatex --shell-escape -interaction=nonstopmode report.tex && \
	  biber report && \
	  lualatex --shell-escape -interaction=nonstopmode report.tex && \
	  lualatex --shell-escape -interaction=nonstopmode report.tex

# ─── Snakemake pipeline (generates cached plots) ─────────────────────────────
plots: venv
	@mkdir -p logs
	$(ACTIVATE) && \
	  env HOME=$(PWD)/.snakemake_cache snakemake --cores 1

# ─── Notebook extraction (auto_nb_code.tex, auto_nb_figures.tex) ──────────────
# Run this once before `make pdf` to make \input{auto_nb_code} etc. work.
notebooks: venv
	$(ACTIVATE) && \
	  python3 pycode/nb_to_report.py pycode/optical_simulator.ipynb

# ─── Python test suite ────────────────────────────────────────────────────────
test-python: venv
	$(ACTIVATE) && \
	  python -m pytest pycode/tests/ -v

# ─── LaTeX macro smoke tests ──────────────────────────────────────────────────
test-macros: venv
	$(ACTIVATE) && \
	  for f in tests/*.tex; do \
	    lualatex -output-directory=tests --shell-escape -interaction=nonstopmode "$$f"; \
	  done

# ─── Run all tests ────────────────────────────────────────────────────────────
test-all: test-python test-macros

# ─── Clean LaTeX aux files ────────────────────────────────────────────────────
clean:
	rm -f *.aux *.bbl *.bcf *.blg *.fdb_latexmk *.fls *.log *.out \
	      *.run.xml *.synctex.gz *.toc *.bbl-SAVE-ERROR
	rm -rf _minted-*

# ─── Full reset: also removes cached plots, notebook extracts, Snakemake state
deepclean: clean
	rm -f plots/*.png plots/*.pdf
	rm -f auto_nb_code.tex auto_nb_figures.tex
	rm -rf pycode/nb_cells/ pycode/nb_snippets/
	rm -rf .snakemake .snakemake_cache logs
