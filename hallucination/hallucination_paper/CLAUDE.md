# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build and Compilation

This is a LaTeX academic paper using ACM SIGCONF format.

**Compile the paper:**
```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

Or use the provided `make.bat` on Windows.

**Generate empirical charts:**
```bash
cd script
python generate_empirical_charts.py
```

**Generate LaTeX tables from CSV:**
```bash
cd script
python generate_table.py
```

## Project Structure

- **main.tex** - Main LaTeX document entry point
- **src/** - Chapter source files and bibliography
  - `ch00-abstract.tex` - Abstract
  - `ch01-introduction.tex` - Introduction
  - `ch02-related-work.tex` - Related work
  - `ch03-empirical.tex` - Empirical study
  - `ch04-approach.tex` - Proposed approach
  - `ch05-evaluation.tex` - Evaluation
  - `reference.bib` - Bibliography
- **data/** - CSV data files for empirical analysis
- **script/** - Python scripts for generating charts and tables
- **figures/** - Figure assets (PDF, PNG)
- **fig/** - Additional figures and diagrams

## Architecture Overview

This repository contains an academic paper about **AutoTrans**, a hierarchical framework for repository-level C++ to Java code translation using LLMs.

**Key components of the approach:**
1. **Static Analysis Phase** - Custom Java parser extracts project structure and call graph dependencies
2. **Hierarchical Translation Phase** - Two-layer translation: Header-level (class design) then Method-level (implementation)
3. **Validation and Repair Phase** - Autonomous compilation agent that iteratively fixes translation errors

**Empirical study setup:**
- Dataset: 6 open-source Java projects (failsafe, jvm-sandbox, easyexcel, httpclient, hutool, Java-WebSocket)
- 24 translation modules covering diverse domains
- Error types tracked: SYNTAX_LANGUAGE_ERROR, TYPE_SYSTEM_ERROR, MISSING_UNDEFINED_SYMBOLS, etc.

## Figures and Tables

- Figures are stored in `figures/` directory with subdirectories for `approach/` and `empirical/`
- Empirical charts are generated from `data/empirical_data.csv` and error distribution CSVs
- Use `\todo{}` command for placeholder text that needs completion

## Dependencies

**LaTeX packages used:**
- `acmart` (ACM conference format)
- `tcolorbox`, `tikz`, `algpseudocode`
- `multirow`, `booktabs`, `tabularx`
- `enumitem`, `microtype`

**Python dependencies for scripts:**
- pandas, matplotlib, seaborn, numpy, chardet
