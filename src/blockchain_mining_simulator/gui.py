from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .chain import Blockchain
from .config import DEFAULT_CONFIG, SimulationConfig
from .layout import TreeLayoutEngine
from .mining import Miner, MiningResult
from .statistics import export_statistics_to_excel
from .svg import SVGExporter


class BlockchainSimulatorApp:
    def __init__(self, root: tk.Tk, config: SimulationConfig | None = None):
        self.root = root
        self.config = config or DEFAULT_CONFIG
        self.blockchain = Blockchain(self.config)
        self.miner = Miner(self.blockchain)
        self.layout_engine = TreeLayoutEngine(self.config)
        self.svg_exporter = SVGExporter(self.config)

        self.next_miner_name = self.config.default_next_miner_name
        self.is_mining = False
        self._mining_thread: threading.Thread | None = None

        self.root.title("Blockchain Mining Simulator")
        self.root.geometry("1280x860")
        self.root.minsize(1080, 720)
        self._build_ui()
        self._prompt_genesis_difficulty()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = ttk.Frame(self.root, padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="Block String").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.block_input = ttk.Entry(top)
        self.block_input.grid(row=0, column=1, sticky="ew", padx=(0, 8))

        ttk.Button(top, text="Add Block", command=self.add_block).grid(row=0, column=2, padx=4)
        self.mine_next_button = ttk.Button(top, text="Search Next Block", command=self.start_mining)
        self.mine_next_button.grid(row=0, column=3, padx=4)

        middle = ttk.Frame(self.root, padding=(12, 0, 12, 0))
        middle.grid(row=1, column=0, sticky="nsew")
        middle.columnconfigure(0, weight=1)
        middle.rowconfigure(1, weight=1)

        ttk.Label(middle, text="Blockchain Visualization").grid(row=0, column=0, sticky="w", pady=(0, 8))

        canvas_wrap = ttk.Frame(middle)
        canvas_wrap.grid(row=1, column=0, sticky="nsew")
        canvas_wrap.columnconfigure(0, weight=1)
        canvas_wrap.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            canvas_wrap,
            background="white",
            scrollregion=(0, 0, self.config.fixed_canvas_width, self.config.fixed_canvas_height),
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(canvas_wrap, orient="vertical", command=self.canvas.yview)
        x_scroll = ttk.Scrollbar(canvas_wrap, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

        bottom = ttk.Frame(self.root, padding=12)
        bottom.grid(row=2, column=0, sticky="ew")
        for idx in range(7):
            bottom.columnconfigure(idx, weight=0)
        bottom.columnconfigure(7, weight=1)

        ttk.Button(bottom, text="Set Next Miner Name", command=self.set_next_miner_name).grid(row=0, column=0, padx=4)
        ttk.Button(bottom, text="Set Difficulty", command=self.set_difficulty).grid(row=0, column=1, padx=4)
        ttk.Button(bottom, text="Copy Latest Block", command=self.copy_latest_block).grid(row=0, column=2, padx=4)
        ttk.Button(bottom, text="Export SVG", command=self.export_svg).grid(row=0, column=3, padx=4)
        ttk.Button(bottom, text="Export Excel Stats", command=self.export_stats).grid(row=0, column=4, padx=4)
        ttk.Button(bottom, text="Clear Blockchain", command=self.clear_blockchain).grid(row=0, column=5, padx=4)
        ttk.Button(bottom, text="Mine Genesis Again", command=self._prompt_genesis_difficulty).grid(row=0, column=6, padx=4)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(bottom, textvariable=self.status_var).grid(row=0, column=7, sticky="w", padx=(12, 0))

    def _prompt_genesis_difficulty(self) -> None:
        if self.blockchain.blocks:
            if not messagebox.askyesno("Reset", "Mining a new genesis block will clear the existing blockchain. Continue?"):
                return
            self.blockchain.clear()
            self.refresh_canvas()

        dialog = tk.Toplevel(self.root)
        dialog.title("Genesis Block Setup")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        ttk.Frame(dialog, padding=16).grid(row=0, column=0, sticky="nsew")
        ttk.Label(dialog, text="Set difficulty for the genesis block").grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        entry = ttk.Entry(dialog)
        entry.insert(0, str(self.blockchain.difficulty))
        entry.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        entry.focus_set()

        def confirm() -> None:
            try:
                difficulty = int(entry.get().strip())
                self.blockchain.clear()
                self.blockchain.set_difficulty(difficulty)
                result = self.miner.mine_genesis_block(difficulty=difficulty)
                self.blockchain.add_block_from_string(result.block_string)
                self.refresh_canvas()
                self.status_var.set(
                    f"Genesis mined | Difficulty={difficulty} | Nonce={result.nonce} | Time={result.elapsed_seconds:.2f}s"
                )
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror("Genesis Mining Failed", str(exc))

        ttk.Button(dialog, text="Mine Genesis Block", command=confirm).grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")

    def refresh_canvas(self) -> None:
        self.canvas.delete("all")
        layout = self.layout_engine.compute(self.blockchain)
        by_hash = {block.hash: block for block in self.blockchain.blocks}

        for block in self.blockchain.blocks:
            if block.height == 0 or block.is_orphan or block.pre not in by_hash:
                continue
            parent = by_hash[block.pre]
            parent_x, parent_y = layout.positions[parent.hash]
            child_x, child_y = layout.positions[block.hash]
            self._draw_connector(parent, block, parent_x, parent_y, child_x, child_y)

        for idx, block in enumerate(self.blockchain.blocks, start=1):
            pos_x, pos_y = layout.positions[block.hash]
            self._draw_block(pos_x, pos_y, block, idx)

        self.status_var.set(
            f"Ready | Total={self.blockchain.total_blocks} | Invalid={self.blockchain.invalid_block_count} | Orphan={self.blockchain.orphan_block_count}"
        )

    def _draw_block(self, x: float, y: float, block, index: int) -> None:
        width = self.config.block_width
        height = self.config.block_height
        border = "#dc143c" if not block.is_valid else "#2e8b57"
        fill = "#fff0f0" if not block.is_valid else "#f8f8ff"
        text_color = "#dc143c" if not block.is_valid else "#00008b"

        self.canvas.create_rectangle(x, y, x + width, y + height, outline=border, width=3, fill=fill)
        self.canvas.create_text(x + 15, y + 15, text=f"#{index}", anchor="nw", fill=border, font=("Arial", 9, "bold"))
        title = "Genesis Block" if block.height == 0 else f"Block (Height={block.height})"
        if block.is_orphan:
            title = f"Orphan Block (Height={block.height})"
        if not block.is_valid:
            title += " (Invalid)"
        self.canvas.create_text(x + width / 2, y + 22, text=title, fill=border, font=("Arial", 9, "bold"))

        lines = [
            f"Pre={block.pre}",
            f"Hash={block.hash}",
            f"Miner={block.miner_name}",
            f"Reward={block.reward}",
            f"Nonce={block.parsed.nonce_raw}",
        ]
        current_y = y + 46
        for line in lines:
            self.canvas.create_text(x + 10, current_y, text=line, anchor="w", fill=text_color, font=("Arial", 8))
            current_y += 18

        if not block.is_valid:
            for error in block.errors[:3]:
                self.canvas.create_text(
                    x + width / 2,
                    current_y,
                    text=f"❌ {error}",
                    fill="#dc143c",
                    font=("Arial", 8),
                )
                current_y += 14

        if block.difficulty_changed:
            self.canvas.create_text(
                x + width / 2,
                y - 18,
                text=f"Difficulty Changed: {self.blockchain.previous_difficulty} → {self.blockchain.difficulty}",
                fill="red",
                font=("Arial", 8),
            )

    def _draw_connector(self, parent, child, parent_x: float, parent_y: float, child_x: float, child_y: float) -> None:
        start_x = parent_x + self.config.block_width / 2
        start_y = parent_y + self.config.block_height
        end_x = child_x + self.config.block_width / 2
        end_y = child_y
        mid_y = (start_y + end_y) / 2
        if not parent.is_valid or not child.is_valid:
            color = "#ff8c00"
            dash = (3, 2)
        elif parent.height + 1 != child.height:
            color = "#dc143c"
            dash = (5, 3)
        else:
            color = "#2e8b57"
            dash = ()
        self.canvas.create_line(start_x, start_y, start_x, mid_y, fill=color, width=2, dash=dash)
        self.canvas.create_line(start_x, mid_y, end_x, mid_y, fill=color, width=2, dash=dash)
        self.canvas.create_line(end_x, mid_y, end_x, end_y, fill=color, width=2, dash=dash)

    def add_block(self) -> None:
        block_string = self.block_input.get().strip()
        if not block_string:
            messagebox.showwarning("Empty", "Please enter a block string.")
            return
        try:
            record = self.blockchain.add_block_from_string(block_string)
            self.refresh_canvas()
            self.block_input.delete(0, tk.END)
            if record.is_valid:
                messagebox.showinfo("Block Added", f"Valid block added at height {record.height}.")
            else:
                messagebox.showinfo("Block Added With Issues", "\n".join(record.errors))
        except Exception as exc:
            messagebox.showerror("Add Block Failed", str(exc))

    def start_mining(self) -> None:
        if self.is_mining:
            messagebox.showwarning("Mining", "Mining is already in progress.")
            return
        if self.blockchain.latest_valid_block() is None:
            messagebox.showwarning("No Parent", "Mine the genesis block first.")
            return
        self.is_mining = True
        self.status_var.set(f"Mining... Difficulty={self.blockchain.difficulty}")

        def worker() -> None:
            try:
                result = self.miner.mine_next_block(miner_name=self.next_miner_name)
                self.root.after(0, lambda: self._show_mining_result(result))
            except Exception as exc:
                self.root.after(0, lambda: messagebox.showerror("Mining Failed", str(exc)))
                self.root.after(0, lambda: self.status_var.set("Mining failed"))
            finally:
                self.is_mining = False

        self._mining_thread = threading.Thread(target=worker, daemon=True)
        self._mining_thread.start()

    def _show_mining_result(self, result: MiningResult) -> None:
        result_msg = f"""Mining Complete! (Height {result.height})
Time: {result.elapsed_seconds:.2f}s
Valid Nonce: {result.nonce}
Hash: {result.block_hash[:20]}...
Full Block String:
{result.block_string}
Copy and paste to add this block"""

        result_window = tk.Toplevel(self.root)
        result_window.title(f"Mining Complete | Height {result.height}")
        result_window.geometry("650x450")
        result_window.resizable(True, True)
        result_window.transient(self.root)

        result_window.grid_rowconfigure(0, weight=1)
        result_window.grid_rowconfigure(1, weight=0)
        result_window.grid_columnconfigure(0, weight=1)

        text_frame = tk.Frame(result_window)
        text_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        scrollbar = ttk.Scrollbar(text_frame, orient="vertical")
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_area = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            yscrollcommand=scrollbar.set,
        )
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text_area.yview)
        text_area.insert(tk.END, result_msg)
        text_area.config(state=tk.DISABLED)

        btn_frame = tk.Frame(result_window)
        btn_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        def copy_result() -> None:
            self.root.clipboard_clear()
            self.root.clipboard_append(result.block_string)
            self.root.update()
            messagebox.showinfo("Copied", "Block string copied to clipboard.")

        tk.Button(
            btn_frame,
            text="Copy Block",
            command=copy_result,
            font=("Arial", 10),
            width=10,
            height=1,
            bg="#e8f4f8",
        ).grid(row=0, column=0, padx=20, pady=5)

        tk.Button(
            btn_frame,
            text="Close",
            command=result_window.destroy,
            font=("Arial", 10),
            width=10,
            height=1,
            bg="#fff5f5",
        ).grid(row=0, column=1, padx=20, pady=5)

        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.status_var.set(f"Mining complete | Height={result.height} | Nonce={result.nonce}")

    def set_next_miner_name(self) -> None:
        self._simple_input_dialog(
            title="Set Next Miner Name",
            prompt="Miner name",
            initial_value=self.next_miner_name,
            on_confirm=lambda value: setattr(self, "next_miner_name", value.strip() or self.next_miner_name),
        )

    def set_difficulty(self) -> None:
        def apply(value: str) -> None:
            self.blockchain.set_difficulty(int(value))
            self.status_var.set(f"Difficulty set to {self.blockchain.difficulty}")

        self._simple_input_dialog(
            title="Set Difficulty",
            prompt="Leading zeros",
            initial_value=str(self.blockchain.difficulty),
            on_confirm=apply,
        )

    def _simple_input_dialog(self, *, title: str, prompt: str, initial_value: str, on_confirm) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.resizable(False, False)

        ttk.Label(dialog, text=prompt).grid(row=0, column=0, padx=16, pady=(16, 8), sticky="w")
        entry = ttk.Entry(dialog)
        entry.insert(0, initial_value)
        entry.grid(row=1, column=0, padx=16, pady=8, sticky="ew")
        entry.focus_set()

        def confirm() -> None:
            try:
                on_confirm(entry.get().strip())
                dialog.destroy()
            except Exception as exc:
                messagebox.showerror(title, str(exc))

        ttk.Button(dialog, text="Confirm", command=confirm).grid(row=2, column=0, padx=16, pady=(8, 16), sticky="ew")

    def copy_latest_block(self) -> None:
        latest = self.blockchain.latest_block()
        if latest is None:
            messagebox.showwarning("Empty", "No blocks available.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(latest.parsed.original)
        self.root.update()
        messagebox.showinfo("Copied", "Latest block copied to clipboard.")

    def export_svg(self) -> None:
        if not self.blockchain.blocks:
            messagebox.showwarning("Empty", "No blocks to export.")
            return
        output_path = filedialog.asksaveasfilename(
            defaultextension=".svg",
            filetypes=[("SVG", "*.svg")],
            title="Export SVG",
        )
        if not output_path:
            return
        self.svg_exporter.export(self.blockchain, output_path)
        messagebox.showinfo("Exported", f"SVG saved to:\n{output_path}")

    def export_stats(self) -> None:
        if not self.blockchain.user_stats:
            messagebox.showwarning("Empty", "No statistics available.")
            return
        output_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Export Statistics",
        )
        if not output_path:
            return
        export_statistics_to_excel(self.blockchain, Path(output_path))
        messagebox.showinfo("Exported", f"Statistics saved to:\n{output_path}")

    def clear_blockchain(self) -> None:
        if not self.blockchain.blocks:
            return
        if messagebox.askyesno("Confirm", "Clear the entire blockchain?"):
            self.blockchain.clear()
            self.refresh_canvas()


def run() -> None:
    root = tk.Tk()
    BlockchainSimulatorApp(root)
    root.mainloop()
