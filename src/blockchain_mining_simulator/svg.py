from __future__ import annotations

from pathlib import Path

from .chain import Blockchain
from .config import SimulationConfig
from .layout import LayoutResult, TreeLayoutEngine


class SVGDocument:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.elements: list[str] = [
            f'<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">',
            """
            <defs>
                <style type="text/css">
                    .font-small { font-family: Arial, Helvetica, sans-serif; font-size: 10.5px; }
                    .font-medium { font-family: Arial, Helvetica, sans-serif; font-size: 12px; }
                </style>
            </defs>
            """,
        ]

    def rect(self, x: float, y: float, width: float, height: float, *, fill: str, stroke: str, stroke_width: int = 1) -> None:
        self.elements.append(
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />'
        )

    def line(self, x1: float, y1: float, x2: float, y2: float, *, stroke: str, stroke_width: int = 1, dash: str = "") -> None:
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        self.elements.append(
            f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{stroke_width}"{dash_attr} />'
        )

    def text(self, x: float, y: float, value: str, *, css_class: str = "font-small", fill: str = "#000000", anchor: str = "start") -> None:
        escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.elements.append(
            f'<text x="{x}" y="{y}" class="{css_class}" fill="{fill}" text-anchor="{anchor}" dominant-baseline="middle">{escaped}</text>'
        )

    def save(self, path: str | Path) -> Path:
        path = Path(path)
        self.elements.append("</svg>")
        path.write_text("".join(self.elements), encoding="utf-8")
        return path


class SVGExporter:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.layout_engine = TreeLayoutEngine(config)

    def export(self, blockchain: Blockchain, path: str | Path) -> Path:
        document = SVGDocument(self.config.fixed_canvas_width, self.config.fixed_canvas_height)
        layout = self.layout_engine.compute(blockchain)
        self._draw_connectors(document, blockchain, layout)
        self._draw_blocks(document, blockchain, layout)
        self._draw_difficulty_labels(document, blockchain, layout)
        return document.save(path)

    def _draw_blocks(self, document: SVGDocument, blockchain: Blockchain, layout: LayoutResult) -> None:
        for index, block in enumerate(blockchain.blocks, start=1):
            pos_x, pos_y = layout.positions[block.hash]
            border = "#dc143c" if not block.is_valid else "#2e8b57"
            fill = "#fff0f0" if not block.is_valid else "#f8f8ff"
            text_color = "#dc143c" if not block.is_valid else "#00008b"
            document.rect(
                pos_x,
                pos_y,
                self.config.block_width,
                self.config.block_height,
                fill=fill,
                stroke=border,
                stroke_width=3,
            )
            document.text(pos_x + 15, pos_y + 15, f"#{index}", css_class="font-medium", fill=border)

            title = "Genesis Block" if block.height == 0 else f"Block (Height={block.height})"
            if block.is_orphan:
                title = f"Orphan Block (Height={block.height})"
            if not block.is_valid:
                title += " (Invalid)"
            document.text(
                pos_x + self.config.block_width / 2,
                pos_y + 22,
                title,
                css_class="font-medium",
                fill=border,
                anchor="middle",
            )

            lines = [
                f"Pre={block.pre}",
                f"Hash={block.hash}",
                f"Miner={block.miner_name}",
                f"Reward={block.reward}",
                f"Nonce={block.parsed.nonce_raw}",
            ]
            current_y = pos_y + 42
            for line in lines:
                document.text(pos_x + 10, current_y, line, fill=text_color)
                current_y += 18
            if not block.is_valid:
                for error in block.errors[:4]:
                    document.text(
                        pos_x + self.config.block_width / 2,
                        current_y,
                        f"❌ {error}",
                        fill="#dc143c",
                        anchor="middle",
                    )
                    current_y += 14

    def _draw_connectors(self, document: SVGDocument, blockchain: Blockchain, layout: LayoutResult) -> None:
        by_hash = {block.hash: block for block in blockchain.blocks}
        for block in blockchain.blocks:
            if block.height == 0 or block.is_orphan or block.pre not in by_hash:
                continue
            parent = by_hash[block.pre]
            parent_x, parent_y = layout.positions[parent.hash]
            child_x, child_y = layout.positions[block.hash]
            start_x = parent_x + self.config.block_width / 2
            start_y = parent_y + self.config.block_height
            end_x = child_x + self.config.block_width / 2
            end_y = child_y
            mid_y = (start_y + end_y) / 2
            if not parent.is_valid or not block.is_valid:
                stroke = "#ff8c00"
                dash = "3,2"
            elif parent.height + 1 != block.height:
                stroke = "#dc143c"
                dash = "5,3"
            else:
                stroke = "#2e8b57"
                dash = ""
            document.line(start_x, start_y, start_x, mid_y, stroke=stroke, stroke_width=2, dash=dash)
            document.line(start_x, mid_y, end_x, mid_y, stroke=stroke, stroke_width=2, dash=dash)
            document.line(end_x, mid_y, end_x, end_y, stroke=stroke, stroke_width=2, dash=dash)

    def _draw_difficulty_labels(self, document: SVGDocument, blockchain: Blockchain, layout: LayoutResult) -> None:
        for block in blockchain.blocks:
            if not block.difficulty_changed:
                continue
            pos_x, pos_y = layout.positions[block.hash]
            label = f"Difficulty Changed: {blockchain.previous_difficulty} → {blockchain.difficulty}"
            label_x = pos_x + self.config.block_width / 2
            label_y = pos_y - 25
            document.rect(label_x - 120, label_y - 10, 240, 20, fill="white", stroke="white")
            document.text(label_x, label_y, label, fill="red", anchor="middle")
