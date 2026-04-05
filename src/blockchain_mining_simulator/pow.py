from __future__ import annotations

import hashlib
from typing import Iterator


def compute_hash(block_string: str) -> str:
    return hashlib.sha256(block_string.encode("utf-8")).hexdigest()


def build_block_string(*, pre: str, height: int, miner_name: str, reward: int, nonce: int | str) -> str:
    return f"Pre={pre}; Height={height}; ->[{miner_name}]:{reward}; Nonce={nonce}"


def meets_difficulty(block_hash: str, difficulty: int) -> bool:
    return block_hash.startswith("0" * difficulty)


def iter_nonce_search(*, pre: str, height: int, miner_name: str, reward: int, start_nonce: int = 0) -> Iterator[tuple[int, str, str]]:
    nonce = start_nonce
    while True:
        block_string = build_block_string(
            pre=pre,
            height=height,
            miner_name=miner_name,
            reward=reward,
            nonce=nonce,
        )
        block_hash = compute_hash(block_string)
        yield nonce, block_string, block_hash
        nonce += 1
