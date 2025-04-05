import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.colors as mcolors
import numpy as np

# Visualization class (Modified to integrate with tkinter)
class MemoryVisualizer:
    def __init__(self):
        # Create matplotlib figure with two subplots
        self.fig, self.axes = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.tight_layout(pad=3.0)
        self.process_colors = {}
        self.color_cycle = iter(mcolors.TABLEAU_COLORS)
        
        # Cache for optimization
        self.memory_patches = []
        self.page_table_patches = []
        
        # Memory axes
        self.memory_ax = self.axes[0]
        self.memory_ax.set_title('Memory Allocation')
        self.memory_ax.set_xlim(0, 1)
        self.memory_ax.set_ylim(0, 1)
        self.memory_ax.set_xticks([])
        self.memory_ax.set_yticks([])
        
        # Page/Segment table axes
        self.table_ax = self.axes[1]
        self.table_ax.set_title('Page/Segment Table')
        self.table_ax.set_xlim(0, 1)
        self.table_ax.set_ylim(0, 1)
        self.table_ax.set_xticks([])
        self.table_ax.set_yticks([])
        
    def get_figure(self):
        """Return the matplotlib figure for embedding in tkinter"""
        return self.fig
    
    def _get_process_color(self, process_id):
        if process_id is None:
            return 'lightgrey'
        if process_id not in self.process_colors:
            try:
                self.process_colors[process_id] = next(self.color_cycle)
            except StopIteration:
                self.process_colors[process_id] = mcolors.to_hex(np.random.rand(3,))
        return self.process_colors[process_id]

    def update_memory_view(self, memory_snapshot, total_memory_size):
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
                text_x = start_pct + width_pct / 2
                text_y = y_pos + height / 2
                text = f"P{block['process_id']}" if block['process_id'] is not None else "Free"
                text_obj = self.memory_ax.text(text_x, text_y, text, ha='center', va='center', fontsize=8)
                self.memory_patches.append(text_obj)
            
            start_text = self.memory_ax.text(start_pct, y_pos - 0.05, f"{block['start']}", 
                                             ha='center', va='top', fontsize=6, rotation=90)
            self.memory_patches.append(start_text)
            
            if block == memory_snapshot[-1]:
                end_text = self.memory_ax.text(start_pct + width_pct, y_pos - 0.05, f"{block['end']}", 
                                               ha='center', va='top', fontsize=6, rotation=90)
                self.memory_patches.append(end_text)
        
        self.memory_ax.set_title('Memory Allocation')

    def update_page_table_view(self, page_table_snapshot, page_size, total_memory_size, method):
        for patch in self.page_table_patches:
            patch.remove()
        self.page_table_patches = []
        
        if method == "paging":
            num_frames = len(page_table_snapshot)
            grid_size = int(np.ceil(np.sqrt(num_frames)))
            cell_width = 1 / grid_size
            cell_height = 1 / grid_size
            
            for i, frame in enumerate(page_table_snapshot):
                row = i // grid_size
                col = i % grid_size
                
                x = col * cell_width
                y = 1 - (row + 1) * cell_height
                
                color = self._get_process_color(frame['process_id'])
                rect = patches.Rectangle((x, y), cell_width * 0.9, cell_height * 0.9,
                                           facecolor=color, edgecolor='black', linewidth=1)
                self.table_ax.add_patch(rect)
                self.page_table_patches.append(rect)
                
                text = f"F{frame['frame_id']}"
                if frame['process_id'] is not None:
                    text += f"\nP{frame['process_id']}"
                text_obj = self.table_ax.text(x + cell_width * 0.45, y + cell_height * 0.45, 
                                              text, ha='center', va='center', fontsize=8)
                self.page_table_patches.append(text_obj)
            
            self.table_ax.set_title('Page Table')
        else:
            segments = [block for block in page_table_snapshot if block['process_id'] is not None]
            num_segments = len(segments)
            if num_segments == 0:
                return
            grid_size = int(np.ceil(np.sqrt(num_segments)))
            cell_width = 1 / grid_size
            cell_height = 1 / grid_size
            
            for i, segment in enumerate(segments):
                row = i // grid_size
                col = i % grid_size
                
                x = col * cell_width
                y = 1 - (row + 1) * cell_height
                
                color = self._get_process_color(segment['process_id'])
                rect = patches.Rectangle((x, y), cell_width * 0.9, cell_height * 0.9,
                                           facecolor=color, edgecolor='black', linewidth=1)
                self.table_ax.add_patch(rect)
                self.page_table_patches.append(rect)
                
                start_addr = segment['start_address']
                end_addr = segment['end_address']
                size = end_addr - start_addr + 1
                
                text = f"P{segment['process_id']}\nAddr: {start_addr}\nSize: {size}"
                text_obj = self.table_ax.text(x + cell_width * 0.45, y + cell_height * 0.45, 
                                              text, ha='center', va='center', fontsize=8)
                self.page_table_patches.append(text_obj)
            
            self.table_ax.set_title('Segment Table')

    def update_visualization(self, memory_snapshot, 
                             page_table_snapshot,
                             stats, events,
                             total_memory_size, page_size,
                             method):
        self.update_memory_view(memory_snapshot, total_memory_size)
        self.update_page_table_view(page_table_snapshot, page_size, total_memory_size, method)

from tkinter import ttk, font

class ModernUI:
    BACKGROUND = "#f5f5f7"
    FRAME_BG = "#ffffff"
    PRIMARY = "#0066cc"
    SECONDARY = "#5ac8fa"
    # Changed SUCCESS from green to blue
    SUCCESS = "#1a73e8"
    WARNING = "#ff9500"
    DANGER = "#ff3b30"
    TEXT = "#1d1d1f"
    SUBTEXT = "#86868b"
    
    @classmethod
    def apply_theme(cls, root):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=cls.FRAME_BG)
        style.configure('TLabel', background=cls.FRAME_BG, foreground=cls.TEXT)
        style.configure('TButton', background=cls.PRIMARY, foreground='white', borderwidth=0)
        style.map('TButton', 
                  background=[('active', cls.SECONDARY), ('pressed', cls.PRIMARY)],
                  relief=[('pressed', 'flat'), ('!pressed', 'flat')])
        
        style.configure('Primary.TButton', background=cls.PRIMARY, foreground='white')
        style.map('Primary.TButton',
                  background=[('active', cls.SECONDARY), ('pressed', cls.PRIMARY)])
        
        style.configure('Success.TButton', background=cls.SUCCESS, foreground='white')
        style.map('Success.TButton',
                  background=[('active', cls.SECONDARY), ('pressed', cls.SUCCESS)])
        
        style.configure('Danger.TButton', background=cls.DANGER, foreground='white')
        style.map('Danger.TButton',
                  background=[('active', '#ff6b60'), ('pressed', cls.DANGER)])
        
        style.configure('TLabelframe', background=cls.FRAME_BG)
        style.configure('TLabelframe.Label', background=cls.FRAME_BG, foreground=cls.PRIMARY, font=('Helvetica', 10, 'bold'))
        
        style.configure('TScale', background=cls.FRAME_BG, troughcolor=cls.SUBTEXT)
        style.configure('TCombobox', background=cls.FRAME_BG, fieldbackground=cls.FRAME_BG)
        style.map('TCombobox', fieldbackground=[('readonly', cls.FRAME_BG)])
        
        root.configure(background=cls.BACKGROUND)
        
        return {
            'title': font.Font(family='Helvetica', size=12, weight='bold'),
            'heading': font.Font(family='Helvetica', size=10, weight='bold'),
            'normal': font.Font(family='Helvetica', size=9),
            'small': font.Font(family='Helvetica', size=8)
        }

