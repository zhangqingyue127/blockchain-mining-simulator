from dataclasses import dataclass


@dataclass(slots=True)
class SimulationConfig:
    fixed_canvas_width: int = 10000
    fixed_canvas_height: int = 25000
    block_width: int = 480
    block_height: int = 160
    vertical_gap: int = 130
    horizontal_gap: int = 1000
    start_x: int = 5000
    start_y: int = 100
    min_difficulty: int = 1
    max_difficulty: int = 10
    default_difficulty: int = 2
    max_height: int = 80
    default_reward: int = 50
    default_next_miner_name: str = "User"


DEFAULT_CONFIG = SimulationConfig()
