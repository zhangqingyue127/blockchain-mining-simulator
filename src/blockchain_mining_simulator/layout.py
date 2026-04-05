from __future__ import annotations

from dataclasses import dataclass

from .chain import Blockchain
from .config import SimulationConfig
from .models import BlockRecord


@dataclass(slots=True)
class LayoutResult:
    positions: dict[str, tuple[float, float]]


class TreeLayoutEngine:
    def __init__(self, config: SimulationConfig):
        self.config = config

    def compute(self, blockchain: Blockchain) -> LayoutResult:
        height_groups = blockchain.grouped_by_height()
        parent_map = blockchain.parent_map()
        positions: dict[str, tuple[float, float]] = {}

        if 0 in height_groups:
            for idx, genesis_block in enumerate(height_groups[0]):
                genesis_x = (
                    self.config.start_x
                    - self.config.block_width / 2
                    + idx * (self.config.horizontal_gap + 50)
                )
                positions[genesis_block.hash] = (genesis_x, self.config.start_y)

        def assign_children(parent_hash: str, parent_pos: tuple[float, float]) -> None:
            children = parent_map.get(parent_hash, [])
            if not children:
                return
            child_count = len(children)
            total_width = (child_count - 1) * self.config.horizontal_gap
            start_x = parent_pos[0] - total_width / 2
            for index, child in enumerate(children):
                child_x = start_x + index * self.config.horizontal_gap
                child_y = parent_pos[1] + self.config.block_height + self.config.vertical_gap
                positions[child.hash] = (child_x, child_y)
                assign_children(child.hash, (child_x, child_y))

        if 0 in height_groups:
            for genesis in height_groups[0]:
                if genesis.hash in positions:
                    assign_children(genesis.hash, positions[genesis.hash])

        self._place_orphans(height_groups, positions)
        return LayoutResult(positions=positions)

    def _place_orphans(
        self,
        height_groups: dict[int, list[BlockRecord]],
        positions: dict[str, tuple[float, float]],
    ) -> None:
        normal_count_by_height: dict[int, int] = {}
        for height, blocks in height_groups.items():
            normal_count_by_height[height] = sum(1 for block in blocks if block.hash in positions)

        for height, blocks in height_groups.items():
            for block in blocks:
                if not block.is_orphan or block.hash in positions:
                    continue
                normal_count = normal_count_by_height.get(height, 0)
                if normal_count > 0:
                    max_normal_x = max(
                        positions[existing.hash][0]
                        for existing in blocks
                        if existing.hash in positions
                    )
                    orphan_x = max_normal_x + self.config.horizontal_gap
                else:
                    orphan_x = self.config.start_x + self.config.horizontal_gap / 2
                orphan_y = self.config.start_y + height * (
                    self.config.block_height + self.config.vertical_gap
                )
                positions[block.hash] = (orphan_x, orphan_y)
                normal_count_by_height[height] = normal_count_by_height.get(height, 0) + 1
