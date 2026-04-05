# Blockchain Mining Simulator

A modular Python project for teaching **blockchain data structures**, **Proof-of-Work (PoW)**, and **fork/orphan visualization**.

This refactored version is designed for GitHub presentation, course submission, and academic-style demonstration. Compared with the original single-file Tkinter implementation, the project now separates:

- blockchain data modeling
- block parsing and validation
- mining logic
- statistics export
- tree-layout computation
- SVG rendering
- Tkinter GUI orchestration
- tests and CLI examples

## Highlights

- **Modular architecture** with a `src/` package layout
- **Proof-of-Work simulation** using SHA-256 and adjustable mining difficulty
- **Interactive GUI** for adding blocks, mining new blocks, exporting SVG, and exporting Excel statistics
- **Fork / orphan block visualization** with explicit error highlighting
- **Reusable core logic** that can be tested independently of the GUI
- **Academic-friendly structure** for experiments, demos, and future extensions

## Project Structure

```text
blockchain-mining-simulator/
├── examples/
│   └── cli_demo.py
├── src/
│   └── blockchain_mining_simulator/
│       ├── __init__.py
│       ├── chain.py
│       ├── config.py
│       ├── gui.py
│       ├── layout.py
│       ├── main.py
│       ├── mining.py
│       ├── models.py
│       ├── parsing.py
│       ├── pow.py
│       ├── statistics.py
│       └── svg.py
├── tests/
│   └── test_parser_and_chain.py
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/blockchain-mining-simulator.git
cd blockchain-mining-simulator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

## Run the GUI

Recommended:

```bash
pip install -e .
python -m blockchain_mining_simulator.main
```

Alternative without editable installation:

```bash
PYTHONPATH=src python -m blockchain_mining_simulator.main
```

## Run the CLI Demo

```bash
python examples/cli_demo.py
```

## Run Tests

```bash
pytest
```

## Typical Workflow

1. Launch the GUI.
2. Set the mining difficulty for the genesis block.
3. Mine the genesis block automatically.
4. Set the next miner name.
5. Click **Search Next Block** to generate a valid block.
6. Add the block directly or copy the generated block string.
7. Export the current chain as SVG or export miner statistics to Excel.

## Core Design

### `pow.py`
Implements SHA-256 hashing, block-string construction, and nonce search.

### `parsing.py`
Parses raw input strings such as:

```text
Pre=<parent_hash>; Height=<height>; ->[Alice]:50; Nonce=12345
```

and performs structural validation.

### `chain.py`
Maintains the blockchain state, difficulty updates, duplicate handling, parent lookup, orphan detection, and user statistics.

### `layout.py`
Computes a deterministic tree layout for valid chains, forks, and orphan blocks.

### `svg.py`
Exports the current visualization to a large fixed-size SVG canvas.

### `gui.py`
Provides the interactive Tkinter application and connects the user interface to the backend modules.

## Recommended Repository Improvements

If you want to polish the GitHub repository even further, the next step could be adding:

- screenshots or GIFs in `docs/`
- GitHub Actions for automated testing
- benchmark scripts for difficulty comparison
- bilingual documentation (English + Chinese)
- a `CITATION.cff` file for academic sharing

## Requirements

- Python 3.10+
- pandas
- openpyxl
- pytest

## Notes

- Tkinter is part of the Python standard library on most desktop Python installations.
- SVG export is independent of the GUI drawing code, so it can be reused in future CLI or web versions.
- The current block-string format is intentionally simple for educational readability.
