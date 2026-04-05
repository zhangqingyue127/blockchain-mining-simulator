from blockchain_mining_simulator.chain import Blockchain
from blockchain_mining_simulator.config import DEFAULT_CONFIG
from blockchain_mining_simulator.mining import Miner
from blockchain_mining_simulator.statistics import build_statistics_dataframe


def main() -> None:
    blockchain = Blockchain(DEFAULT_CONFIG)
    blockchain.set_difficulty(2)
    miner = Miner(blockchain)

    genesis = miner.mine_genesis_block(difficulty=2)
    blockchain.add_block_from_string(genesis.block_string)

    alice = miner.mine_next_block(miner_name="Alice")
    blockchain.add_block_from_string(alice.block_string)

    bob = miner.mine_next_block(miner_name="Bob")
    blockchain.add_block_from_string(bob.block_string)

    print("Latest valid block height:", blockchain.latest_valid_block().height)
    print(build_statistics_dataframe(blockchain).to_string(index=False))


if __name__ == "__main__":
    main()
