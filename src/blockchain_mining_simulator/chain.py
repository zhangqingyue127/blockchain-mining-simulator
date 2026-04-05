from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .config import SimulationConfig
from .models import BlockRecord, ParsedBlockInput, UserStats
from .parsing import BlockParser


class Blockchain:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.parser = BlockParser(config)
        self.blocks: list[BlockRecord] = []
        self.user_stats: dict[str, UserStats] = {}
        self.difficulty = config.default_difficulty
        self.previous_difficulty = config.default_difficulty
        self.pending_diff_block_hash: str | None = None
        self.difficulty_change_pending = False

    def clear(self) -> None:
        self.blocks.clear()
        self.user_stats.clear()
        self.difficulty = self.config.default_difficulty
        self.previous_difficulty = self.config.default_difficulty
        self.pending_diff_block_hash = None
        self.difficulty_change_pending = False

    def set_difficulty(self, new_difficulty: int) -> None:
        if not (self.config.min_difficulty <= new_difficulty <= self.config.max_difficulty):
            raise ValueError(
                f"Difficulty must be between {self.config.min_difficulty} and {self.config.max_difficulty}."
            )
        if new_difficulty != self.difficulty:
            self.previous_difficulty = self.difficulty
            self.difficulty = new_difficulty
            self.difficulty_change_pending = True
            self.pending_diff_block_hash = None

    def add_block_from_string(self, block_string: str) -> BlockRecord:
        parsed, parsing_errors = self.parser.parse(block_string)
        if parsed is None:
            raise ValueError("Block string could not be parsed.")
        return self.add_parsed_block(parsed, parsing_errors)

    def add_parsed_block(self, parsed: ParsedBlockInput, parsing_errors: Iterable[str] | None = None) -> BlockRecord:
        known_hashes = {block.hash for block in self.blocks}
        parent_height_lookup = {block.hash: block.height for block in self.blocks}
        errors = self.parser.validate_structure(
            parsed,
            parsing_errors or [],
            difficulty=self.difficulty,
            known_hashes=known_hashes,
            parent_height_lookup=parent_height_lookup,
        )
        if parsed.pre in parent_height_lookup:
            parent_record = self.get_block_by_hash(parsed.pre)
            if parent_record is not None and not parent_record.is_valid:
                parent_hint = f"Parent is invalid (Hash={parsed.pre[:8]}...)"
                if parent_hint not in errors:
                    errors.append(parent_hint)

        difficulty_changed = self.difficulty_change_pending and self.pending_diff_block_hash is None
        record = BlockRecord(parsed=parsed, errors=errors, difficulty_changed=difficulty_changed)
        if record.hash not in known_hashes:
            self.blocks.append(record)
            if difficulty_changed:
                self.pending_diff_block_hash = record.hash
                self.difficulty_change_pending = False
        self._register_stats(record)
        return record

    def _register_stats(self, record: BlockRecord) -> None:
        stats = self.user_stats.setdefault(record.miner_name, UserStats())
        stats.register(record.reward, record.is_valid)

    def get_block_by_hash(self, block_hash: str) -> BlockRecord | None:
        for block in self.blocks:
            if block.hash == block_hash:
                return block
        return None

    def valid_blocks(self) -> list[BlockRecord]:
        return [block for block in self.blocks if block.is_valid]

    def latest_valid_block(self) -> BlockRecord | None:
        valid = self.valid_blocks()
        if not valid:
            return None
        return max(valid, key=lambda block: block.height)

    def latest_block(self) -> BlockRecord | None:
        if not self.blocks:
            return None
        return max(self.blocks, key=lambda block: block.height)

    def grouped_by_height(self) -> dict[int, list[BlockRecord]]:
        groups: dict[int, list[BlockRecord]] = defaultdict(list)
        for block in self.blocks:
            groups[block.height].append(block)
        return dict(groups)

    def parent_map(self) -> dict[str, list[BlockRecord]]:
        mapping: dict[str, list[BlockRecord]] = defaultdict(list)
        for block in self.blocks:
            mapping[block.pre].append(block)
        return dict(mapping)

    @property
    def total_blocks(self) -> int:
        return len(self.blocks)

    @property
    def invalid_block_count(self) -> int:
        return sum(1 for block in self.blocks if not block.is_valid)

    @property
    def orphan_block_count(self) -> int:
        return sum(1 for block in self.blocks if block.is_orphan)
