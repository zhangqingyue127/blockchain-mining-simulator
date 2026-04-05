from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ParsedBlockInput:
    pre: str
    height: int
    miner_name: str
    reward: int
    nonce_raw: str
    original: str
    block_hash: str

    @property
    def nonce(self) -> int | None:
        return int(self.nonce_raw) if self.nonce_raw.isdigit() else None


@dataclass(slots=True)
class BlockRecord:
    parsed: ParsedBlockInput
    errors: list[str] = field(default_factory=list)
    difficulty_changed: bool = False

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    @property
    def is_orphan(self) -> bool:
        return any("Parent not found" in err for err in self.errors)

    @property
    def hash(self) -> str:
        return self.parsed.block_hash

    @property
    def pre(self) -> str:
        return self.parsed.pre

    @property
    def height(self) -> int:
        return self.parsed.height

    @property
    def miner_name(self) -> str:
        return self.parsed.miner_name

    @property
    def reward(self) -> int:
        return self.parsed.reward


@dataclass(slots=True)
class UserStats:
    total_reward: int = 0
    mined_count: int = 0
    valid_count: int = 0

    def register(self, reward: int, is_valid: bool) -> None:
        self.total_reward += reward
        self.mined_count += 1
        if is_valid:
            self.valid_count += 1

    @property
    def success_rate(self) -> float:
        if self.mined_count == 0:
            return 0.0
        return self.valid_count / self.mined_count

    def to_dict(self, username: str, rank: int | None = None) -> dict[str, Any]:
        result = {
            "Username": username,
            "Total Reward": self.total_reward,
            "Mined Blocks": self.mined_count,
            "Valid Blocks": self.valid_count,
            "Success Rate": f"{self.success_rate:.2%}",
        }
        if rank is not None:
            result = {"Rank": rank, **result}
        return result
