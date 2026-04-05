# Blockchain Mining Simulator

> This project was developed as a course experiment for the junior-year first-semester course **“Blockchain Technology (Financial Certification-Theory and Practice)”**.

An educational Python project for simulating blockchain mining, Proof-of-Work (PoW), fork formation, and blockchain visualization.

Built with a Tkinter GUI and a modular code structure, this project is designed for teaching, demonstrations, and introductory blockchain experiments.


## Highlights

- Proof-of-Work mining with adjustable difficulty
- Genesis block generation and next-block mining
- Validation of block structure, hash, height, and parent linkage
- Visualization of main chain, forks, and orphan blocks
- SVG export for blockchain diagrams
- Excel export for miner statistics
- Modular architecture for easier extension and maintenance

## Project Structure

```text
blockchain-mining-simulator/
├── README.md
├── pyproject.toml
├── requirements.txt
├── examples/
├── tests/
└── src/
    └── blockchain_mining_simulator/
        ├── main.py
        ├── gui.py
        ├── chain.py
        ├── config.py
        ├── layout.py
        ├── mining.py
        ├── parsing.py
        ├── statistics.py
        └── svg.py
````

## Installation

```bash
git clone https://github.com/zhangqingyue127/blockchain-mining-simulator.git
cd blockchain-mining-simulator
pip install -r requirements.txt
pip install -e .
```

## Run

```bash
python -m blockchain_mining_simulator.main
```

## What This Project Demonstrates

* how Proof-of-Work mining searches for a valid nonce
* how parent hashes connect blocks into a chain
* how forks and orphan blocks emerge
* how invalid blocks can still be visualized for analysis
* how difficulty changes affect mining behavior

## Main Features

### Simulation

* user-defined genesis difficulty
* next-block auto mining
* manual block insertion
* difficulty adjustment
* invalid block detection

### Visualization

* tree-style blockchain layout
* color-coded valid and invalid blocks
* fork and orphan display
* difficulty-change markers

### Export

* SVG visualization export
* Excel leaderboard/statistics export

## Example Workflow

1. Launch the application
2. Mine the genesis block
3. Set the next miner name
4. Search for the next valid block
5. Copy the mined block string
6. Add the block to the chain
7. Observe the updated blockchain graph

## Testing

```bash
pytest
```

## Example CLI Demo

```bash
python examples/cli_demo.py
```

## Notes

This is an educational simulator, not a production blockchain implementation. It does not include networking, distributed consensus, wallets, signatures, or transaction pools.

## License

No license file is currently included. Add one if you want to define reuse permissions.

## Author

Zhang Qingyue

GitHub: `https://github.com/zhangqingyue127/blockchain-mining-simulator`

```
```
