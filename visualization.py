# visualization.py

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import numpy as np
from typing import Dict, List, Optional
import time
from matplotlib.figure import Figure

class MemoryVisualizer:
    def __init__(self, figure_size=(10, 8)):
        self.fig = Figure(figsize=figure_size)
        self.axes = self.fig.subplots(2, 1)
        self.fig.tight_layout(pad=3.0)
        self.process_colors = {}
        self.color_cycle = iter(mcolors.TABLEAU_COLORS)
        
        # Cache for optimization
        self.memory_patches = []
        self.page_table_patches = []
        
        # Text positions
        self.stats_text = self.fig.text(0.02, 0.02, "", fontsize=8)
        self.events_text = self.fig.text(0.55, 0.02, "", fontsize=8)
        
        # Memory axes setup
        self.memory_ax = self.axes[0]
        self._setup_axes(self.memory_ax, 'Memory Allocation')
        
        # Page/Segment table axes setup
        self.table_ax = self.axes[1]
        self._setup_axes(self.table_ax, 'Page/Segment Table')
        
        # Adjust layout
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    def _setup_axes(self, ax, title):
        ax.set_title(title)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])

    def _get_process_color(self, process_id: Optional[int]) -> str:
        if process_id is None:
            return 'lightgrey'
        
        if process_id not in self.process_colors:
            try:
                self.process_colors[process_id] = next(self.color_cycle)
            except StopIteration:
                self.process_colors[process_id] = mcolors.to_hex(np.random.rand(3,))
        return self.process_colors[process_id]

    def update_memory_view(self, memory_snapshot: List[Dict], total_memory_size: int):
        for patch in self.memory_patches:
            patch.remove()
        self.memory_patches = []
        
        height = 0.6
        y_pos = 0.2
        
        for block in memory_snapshot:
            start_pct = block['start'] / total_memory_size
            width_pct = block['size'] / total_memory_size
            
            color = self._get_process_color(block['process_id'])
            rect = patches.Rectangle((start_pct, y_pos), width_pct, height, 
                                   facecolor=color, edgecolor='black', linewidth=1)
            self.memory_ax.add_patch(rect)
            self.memory_patches.append(rect)
            
            if block['size'] / total_memory_size > 0.05:
                text = f"P{block['process_id']}" if block['process_id'] else "Free"
                text_obj = self.memory_ax.text(start_pct + width_pct/2, y_pos + height/2, 
                                              text, ha='center', va='center', fontsize=8)
                self.memory_patches.append(text_obj)

    def update_page_table_view(self, page_table_snapshot: List[Dict], page_size: int,
                              total_memory_size: int, method: str):
        for patch in self.page_table_patches:
            patch.remove()
        self.page_table_patches = []
        
        if method == "paging":
            num_frames = len(page_table_snapshot)
            grid_size = int(np.ceil(np.sqrt(num_frames)))
            cell_size = 1 / grid_size
            
            for i, frame in enumerate(page_table_snapshot):
                row, col = divmod(i, grid_size)
                x = col * cell_size
                y = 1 - (row + 1) * cell_size
                
                color = self._get_process_color(frame['process_id'])
                rect = patches.Rectangle((x, y), cell_size*0.9, cell_size*0.9,
                                       facecolor=color, edgecolor='black', linewidth=1)
                self.table_ax.add_patch(rect)
                self.page_table_patches.append(rect)
                
                text = f"F{frame['frame_id']}\nP{frame['process_id']}" if frame['process_id'] else f"F{frame['frame_id']}"
                text_obj = self.table_ax.text(x + cell_size*0.45, y + cell_size*0.45, 
                                            text, ha='center', va='center', fontsize=8)
                self.page_table_patches.append(text_obj)

    def update_stats(self, stats: Dict):
        stats_str = (
            f"Memory Statistics:\n"
            f"Total: {stats['total_memory']} units\n"
            f"Used: {stats['used_memory']} ({stats['used_percentage']:.1f}%)\n"
            f"Free: {stats['free_memory']}\n"
            f"Page Faults: {stats['page_faults']}\n"
            f"Ext. Frag: {stats['external_fragmentation']:.2f}\n"
            f"Int. Frag: {stats['internal_fragmentation']}\n"
            f"Processes: {stats['process_count']}"
        )
        self.stats_text.set_text(stats_str)

    def update_events(self, events: List[Dict]):
        events_str = "Recent Events:\n"
        for event in events[-5:]:
            time_str = time.strftime('%H:%M:%S', time.localtime(event['timestamp']))
            events_str += f"{time_str} - {event['event_type']}: P{event['process_id']}\n"
        self.events_text.set_text(events_str)

    def clear(self):
        self.fig.clf()