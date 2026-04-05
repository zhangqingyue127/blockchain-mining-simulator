from __future__ import annotations

import time
from dataclasses import dataclass

from .chain import Blockchain
from .pow import build_block_string, iter_nonce_search, meets_difficulty


@dataclass(slots=True)
class MiningResult:
    block_string: str
    block_hash: str
    nonce: int
    elapsed_seconds: float
    height: int
    difficulty: int


class Miner:
    def __init__(self, blockchain: Blockchain):
        self.blockchain = blockchain

    def mine_genesis_block(self, difficulty: int | None = None, reward: int | None = None) -> MiningResult:
        difficulty = self.blockchain.difficulty if difficulty is None else difficulty
        reward = self.blockchain.config.default_reward if reward is None else reward
        start_time = time.time()

        for nonce, block_string, block_hash in iter_nonce_search(
            pre="HelloMiner",
            height=0,
            miner_name="Genesis",
            reward=reward,
            start_nonce=0,
        ):
            if meets_difficulty(block_hash, difficulty):
                elapsed = time.time() - start_time
                return MiningResult(
                    block_string=block_string,
                    block_hash=block_hash,
                    nonce=nonce,
                    elapsed_seconds=elapsed,
                    height=0,
                    difficulty=difficulty,
                )
        raise RuntimeError("Failed to mine genesis block.")

    def mine_next_block(
        self,
        *,
        miner_name: str,
        reward: int | None = None,
        start_nonce: int = 0,
    ) -> MiningResult:
        base_block = self.blockchain.latest_valid_block()
        if base_block is None:
            raise ValueError("No valid parent block exists. Mine the genesis block first.")

        reward = base_block.reward if reward is None else reward
        target_height = base_block.height + 1
        difficulty = self.blockchain.difficulty
        start_time = time.time()

        for nonce, block_string, block_hash in iter_nonce_search(
            pre=base_block.hash,
            height=target_height,
            miner_name=miner_name,
            reward=reward,
            start_nonce=start_nonce,
        ):
            if meets_difficulty(block_hash, difficulty):
                elapsed = time.time() - start_time
                return MiningResult(
                    block_string=block_string,
                    block_hash=block_hash,
                    nonce=nonce,
                    elapsed_seconds=elapsed,
                    height=target_height,
                    difficulty=difficulty,
                )
        raise RuntimeError("Failed to mine next block.")

    @staticmethod
    def preview_next_block_string(*, parent_hash: str, height: int, miner_name: str, reward: int, nonce: int) -> str:
        return build_block_string(
            pre=parent_hash,
            height=height,
            miner_name=miner_name,
            reward=reward,
            nonce=nonce,
        )
