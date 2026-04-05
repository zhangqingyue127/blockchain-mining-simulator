from __future__ import annotations

from typing import Iterable

from .config import SimulationConfig
from .models import ParsedBlockInput
from .pow import compute_hash, meets_difficulty


class BlockParser:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def parse(self, block_string: str) -> tuple[ParsedBlockInput | None, list[str]]:
        block_string = block_string.strip()
        if not block_string:
            return None, ["Empty block string"]

        parts = [part.strip() for part in block_string.split(";") if part.strip()]
        errors: list[str] = []

        pre_value = self._extract_pre(parts, errors)
        height = self._extract_height(parts, errors)
        miner_name, reward = self._extract_miner_and_reward(parts, errors)
        nonce_raw = self._extract_nonce(parts, errors)
        block_hash = compute_hash(block_string)

        parsed = ParsedBlockInput(
            pre=pre_value,
            height=height,
            miner_name=miner_name,
            reward=reward,
            nonce_raw=nonce_raw,
            original=block_string,
            block_hash=block_hash,
        )
        return parsed, errors

    def validate_structure(
        self,
        parsed: ParsedBlockInput,
        preliminary_errors: Iterable[str],
        *,
        difficulty: int,
        known_hashes: set[str],
        parent_height_lookup: dict[str, int],
    ) -> list[str]:
        errors = list(preliminary_errors)

        if not meets_difficulty(parsed.block_hash, difficulty):
            errors.append(f"Hash does not meet difficulty (Needs {difficulty} leading zeros)")

        if parsed.height >= self.config.max_height:
            errors.append(
                f"Height limit exceeded (Max {self.config.max_height}, Current: {parsed.height})"
            )

        if parsed.height > 0 and parsed.pre not in known_hashes and parsed.pre != "Missing Pre":
            errors.append(f"Parent not found (Pre={parsed.pre[:8]}...)")

        if parsed.height > 0 and parsed.pre in parent_height_lookup:
            parent_height = parent_height_lookup[parsed.pre]
            if parent_height + 1 != parsed.height:
                errors.append(f"Height mismatch (Parent={parent_height}, Current={parsed.height})")

        return errors

    @staticmethod
    def _extract_pre(parts: list[str], errors: list[str]) -> str:
        try:
            return next(part.split("=", 1)[1] for part in parts if part.startswith("Pre="))
        except StopIteration:
            errors.append("Missing Pre field (Pre=parent_hash)")
            return "Missing Pre"

    @staticmethod
    def _extract_height(parts: list[str], errors: list[str]) -> int:
        try:
            value = next(part.split("=", 1)[1] for part in parts if part.startswith("Height="))
        except StopIteration:
            errors.append("Missing Height field (Height=number)")
            return 0

        if not value.isdigit():
            errors.append(f"Height must be number (Got: {value})")
            return 0
        return int(value)

    @staticmethod
    def _extract_miner_and_reward(parts: list[str], errors: list[str]) -> tuple[str, int]:
        try:
            name_part = next(part for part in parts if part.startswith("->["))
        except StopIteration:
            errors.append("Missing name field (->[name]:reward)")
            return "Missing Name", 0

        if "[" not in name_part or "]" not in name_part or ":" not in name_part:
            errors.append("Invalid name format (->[name]:reward)")
            return "Missing Name", 0

        miner_name = name_part.split("[", 1)[1].split("]", 1)[0].strip() or "Unnamed"
        reward_raw = name_part.split(":", 1)[1].strip()
        if not reward_raw.isdigit():
            errors.append(f"Reward must be number (Got: {reward_raw})")
            reward = 0
        else:
            reward = int(reward_raw)
        return miner_name, reward

    @staticmethod
    def _extract_nonce(parts: list[str], errors: list[str]) -> str:
        try:
            nonce_raw = next(part.split("=", 1)[1] for part in parts if part.startswith("Nonce="))
        except StopIteration:
            errors.append("Invalid Nonce")
            return "Missing Nonce"

        if not nonce_raw.isdigit():
            errors.append("Invalid Nonce")
        return nonce_raw
