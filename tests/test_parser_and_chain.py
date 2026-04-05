from blockchain_mining_simulator.chain import Blockchain
from blockchain_mining_simulator.config import DEFAULT_CONFIG
from blockchain_mining_simulator.mining import Miner


def test_genesis_and_next_block_are_valid():
    chain = Blockchain(DEFAULT_CONFIG)
    chain.set_difficulty(2)
    miner = Miner(chain)

    genesis = miner.mine_genesis_block(difficulty=2)
    genesis_record = chain.add_block_from_string(genesis.block_string)
    assert genesis_record.is_valid
    assert genesis_record.height == 0

    second = miner.mine_next_block(miner_name="Alice")
    second_record = chain.add_block_from_string(second.block_string)
    assert second_record.is_valid
    assert second_record.height == 1
    assert chain.latest_valid_block() is not None
    assert chain.latest_valid_block().height == 1


def test_invalid_parent_is_detected():
    chain = Blockchain(DEFAULT_CONFIG)
    chain.set_difficulty(1)
    record = chain.add_block_from_string("Pre=abcdef; Height=1; ->[Alice]:50; Nonce=0")
    assert not record.is_valid
    assert any("Parent not found" in error for error in record.errors)
