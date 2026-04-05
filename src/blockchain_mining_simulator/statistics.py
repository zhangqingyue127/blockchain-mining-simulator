from __future__ import annotations

from pathlib import Path

import pandas as pd

from .chain import Blockchain


def build_statistics_dataframe(blockchain: Blockchain) -> pd.DataFrame:
    rows = []
    ranking = sorted(
        blockchain.user_stats.items(),
        key=lambda item: item[1].total_reward,
        reverse=True,
    )
    for rank, (username, stats) in enumerate(ranking, start=1):
        rows.append(stats.to_dict(username=username, rank=rank))
    return pd.DataFrame(rows)


def export_statistics_to_excel(blockchain: Blockchain, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    dataframe = build_statistics_dataframe(blockchain)
    dataframe.to_excel(output_path, index=False, engine="openpyxl")
    return output_path
