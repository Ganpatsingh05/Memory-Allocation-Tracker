import tkinter as tk
from tkinter import ttk, scrolledtext, font
import threading
import time
import random
from typing import Dict, List, Optional, Tuple
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import from our memory_allocation_engine module
from memory_allocation_engine import MemoryManager, ProcessGenerator, AllocationMethod
# Import visualization classes
from visualization import MemoryVisualizer, ModernUI

# Memory Visualizer GUI
class MemoryVisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Allocation Visualizer")
        self.root.geometry("1280x800")
        
        self.fonts = ModernUI.apply_theme(root)
        
        self.memory_size = 256
        self.page_size = 16
        self.memory_manager = MemoryManager(self.memory_size, self.page_size)
        self.visualizer = MemoryVisualizer()
        self.process_generator = ProcessGenerator(4, 64)
        self.allocated_process_ids = set()
        
        self.allocation_method = AllocationMethod.PAGING
        
        self.simulation_running = False
        self.simulation_thread = None
        self.simulation_speed = 1.0
        self.auto_generate_processes = False # New flag for auto process generation
        
        
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.main_frame.columnconfigure(0, weight=0)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=0)
        self.main_frame.rowconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=0)
        
        self._create_header()
        self._create_control_panel()
        self._create_process_panel()
        self._create_visualization_panel()
        self._create_log_panel()
        self._create_stats_panel()
        
        self._update_visualization()
    
    def _create_header(self):
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 15))
        
        title_label = ttk.Label(header_frame, text="Memory Allocation Visualizer", 
                                font=self.fonts['title'], foreground=ModernUI.PRIMARY)
        title_label.pack(anchor="w")
        
        description = "Interactive visualization of memory allocation strategies: paging and segmentation"
        desc_label = ttk.Label(header_frame, text=description, foreground=ModernUI.SUBTEXT)
        desc_label.pack(anchor="w")
        
        separator = ttk.Separator(self.main_frame, orient='horizontal')
        separator.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(40, 0))
    
    def _create_control_panel(self):
        left_panel = ttk.Frame(self.main_frame)
        left_panel.grid(row=1, column=0, padx=(0, 15), sticky="ns")
        
        control_frame = ttk.LabelFrame(left_panel, text="Simulation Controls")
        control_frame.pack(fill=tk.X, padx=0, pady=(0, 15))
        
        controls_grid = ttk.Frame(control_frame)
        controls_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(controls_grid, text="Memory Size:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.memory_size_var = tk.StringVar(value=str(self.memory_size))
        memory_size_entry = ttk.Entry(controls_grid, width=10, textvariable=self.memory_size_var)
        memory_size_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(controls_grid, text="Page Size:").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_entry = ttk.Entry(controls_grid, width=10, textvariable=self.page_size_var)
        page_size_entry.grid(row=1, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(controls_grid, text="Allocation Method:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.allocation_method_var = tk.StringVar(value="paging")
        allocation_method_combo = ttk.Combobox(controls_grid, textvariable=self.allocation_method_var, 
                                               values=["paging", "segmentation"], state="readonly", width=12)
        allocation_method_combo.grid(row=2, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(controls_grid, text="Simulation Speed:").grid(row=3, column=0, padx=5, pady=8, sticky="w")
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_frame = ttk.Frame(controls_grid)
        speed_frame.grid(row=3, column=1, padx=5, pady=8, sticky="w")
        
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, 
                                 variable=self.speed_var, length=100)
        speed_scale.pack(side=tk.LEFT)
        
        speed_label = ttk.Label(speed_frame, text="1.0s")
        speed_label.pack(side=tk.LEFT, padx=(5, 0))
        
        def update_speed_label(*args):
            speed_label.config(text=f"{self.speed_var.get():.1f}s")
        self.speed_var.trace_add("write", update_speed_label)
        
        # Add auto-generate processes checkbox
        self.auto_generate_var = tk.BooleanVar(value=False)
        auto_generate_check = ttk.Checkbutton(controls_grid, text="Auto-generate processes",
                                             variable=self.auto_generate_var,
                                             command=self._toggle_auto_generate)
        auto_generate_check.grid(row=4, column=0, columnspan=2, padx=5, pady=8, sticky="w")
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        reset_button = ttk.Button(button_frame, text="Reset", style="Danger.TButton", command=self._reset_simulation)
        reset_button.pack(side=tk.LEFT, padx=(0, 5), pady=5, fill=tk.X, expand=True)
        
        apply_button = ttk.Button(button_frame, text="Apply Settings", style="Primary.TButton", command=self._apply_settings)
        apply_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Add a Start/Stop Simulation button
        self.start_stop_var = tk.StringVar(value="Start Simulation")
        self.start_stop_button = ttk.Button(control_frame, textvariable=self.start_stop_var,
                                            style="Success.TButton", command=self._toggle_simulation)
        self.start_stop_button.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def _toggle_auto_generate(self):
        """Toggle auto-generation of processes"""
        self.auto_generate_processes = self.auto_generate_var.get()
        if self.auto_generate_processes:
            self._log_message("Auto-generate processes enabled", "info")
        else:
            self._log_message("Auto-generate processes disabled", "info")
    
    def _create_process_panel(self):
        left_panel = self.main_frame.grid_slaves(row=1, column=0)[0]
        process_frame = ttk.LabelFrame(left_panel, text="Process Management")
        process_frame.pack(fill=tk.X, padx=0, pady=0)
        
        process_grid = ttk.Frame(process_frame)
        process_grid.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(process_grid, text="Process Size:").grid(row=0, column=0, padx=5, pady=8, sticky="w")
        self.process_size_var = tk.StringVar(value="32")
        process_size_entry = ttk.Entry(process_grid, width=10, textvariable=self.process_size_var)
        process_size_entry.grid(row=0, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(process_grid, text="Process Lifetime (s):").grid(row=1, column=0, padx=5, pady=8, sticky="w")
        self.process_lifetime_var = tk.StringVar(value="10")
        process_lifetime_entry = ttk.Entry(process_grid, width=10, textvariable=self.process_lifetime_var)
        process_lifetime_entry.grid(row=1, column=1, padx=5, pady=8, sticky="w")
        
        ttk.Label(process_grid, text="Process ID:").grid(row=2, column=0, padx=5, pady=8, sticky="w")
        self.process_id_var = tk.StringVar()
        process_id_entry = ttk.Entry(process_grid, width=10, textvariable=self.process_id_var)
        process_id_entry.grid(row=2, column=1, padx=5, pady=8, sticky="w")
        
        button_frame = ttk.Frame(process_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        add_process_button = ttk.Button(button_frame, text="Add Process", style="Primary.TButton", command=self._add_process)
        add_process_button.pack(side=tk.LEFT, padx=(0, 5), pady=5, fill=tk.X, expand=True)
        
        remove_process_button = ttk.Button(button_frame, text="Remove Process", style="Danger.TButton", command=self._remove_process)
        remove_process_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        random_process_button = ttk.Button(process_frame, text="Add Random Process", style="Success.TButton", command=self._add_random_process)
        random_process_button.pack(fill=tk.X, padx=10, pady=(0, 10))
    
    def _create_visualization_panel(self):
        vis_frame = ttk.LabelFrame(self.main_frame, text="Memory Visualization")
        vis_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 0), pady=(0, 15))
        
        self.canvas = FigureCanvasTkAgg(self.visualizer.get_figure(), master=vis_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _create_log_panel(self):
        log_frame = ttk.LabelFrame(self.main_frame, text="Event Log")
        log_frame.grid(row=2, column=1, sticky="ew", padx=(0, 0), pady=(0, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=50, height=8, font=self.fonts['small'])
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.log_text.tag_configure("timestamp", foreground=ModernUI.SUBTEXT)
        self.log_text.tag_configure("success", foreground=ModernUI.SUCCESS)
        self.log_text.tag_configure("error", foreground=ModernUI.DANGER)
        self.log_text.tag_configure("info", foreground=ModernUI.PRIMARY)
        self._log_message("Memory Allocation Visualizer started", "info")
    
    def _create_stats_panel(self):
        stats_frame = ttk.LabelFrame(self.main_frame, text="Memory Statistics")
        stats_frame.grid(row=2, column=0, sticky="nsew", padx=(0, 15), pady=(0, 0))
        
        self.stats_text = tk.Text(stats_frame, height=12, width=30, font=self.fonts['small'])
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.stats_text.configure(state="disabled")
    
    def _update_visualization(self):
        memory_snapshot = self.memory_manager.get_memory_snapshot()
        page_table_snapshot = self.memory_manager.get_page_table_snapshot()
        stats = self.memory_manager.get_memory_stats()
        events = self.memory_manager.get_recent_events()
        
        method = self.allocation_method_var.get()
        self.visualizer.update_visualization(memory_snapshot, page_table_snapshot, stats, events,
                                             self.memory_size, self.page_size, method)
        self.canvas.draw_idle()
        self._update_stats(stats)
        self._update_log(events)
        self.root.after(100, self._update_visualization)
    
    def _update_stats(self, stats):
        self.stats_text.configure(state="normal")
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, "Memory Utilization\n", "heading")
        self.stats_text.insert(tk.END, f"Total Memory: {stats.get('total_memory', 0)} units\n")
        self.stats_text.insert(tk.END, f"Used Memory: {stats.get('used_memory', 0)} units\n")
        self.stats_text.insert(tk.END, f"Free Memory: {stats.get('free_memory', 0)} units\n")
        utilization = 0
        if stats.get('total_memory', 0) > 0:
            utilization = (stats.get('used_memory', 0) / stats.get('total_memory', 0)) * 100
        self.stats_text.insert(tk.END, f"Utilization: {utilization:.1f}%\n\n")
        self.stats_text.insert(tk.END, "Active Processes\n", "heading")
        self.stats_text.insert(tk.END, f"Process Count: {stats.get('process_count', 0)}\n")
        # Display fragmentation information
        self.stats_text.insert(tk.END, f"External Fragmentation: {stats.get('external_fragmentation', 0):.2f}\n")
        self.stats_text.insert(tk.END, f"Internal Fragmentation: {stats.get('internal_fragmentation', 0)} units\n")
        self.stats_text.tag_configure("heading", font=self.fonts['heading'], foreground=ModernUI.PRIMARY)
        self.stats_text.configure(state="disabled")
    
    def _update_log(self, events):
        # This method can be expanded if you want to show recent events in the stats panel.
        pass
    
    def _log_message(self, message, message_type="info"):
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{message}\n", message_type)
        self.log_text.see(tk.END)
    
    def _toggle_simulation(self):
        if self.simulation_running:
            self.simulation_running = False
            self.start_stop_var.set("Start Simulation")
            self._log_message("Simulation stopped", "info")
        else:
            self.simulation_running = True
            self.start_stop_var.set("Stop Simulation")
            self._log_message("Simulation started", "success")

            # Allocate pending processes when simulation starts
            if hasattr(self, 'pending_processes'):
                for process_id, size, method, lifetime in self.pending_processes:
                    success = self.memory_manager.allocate_process(process_id, size, method)
                    if success:
                        self._log_message(f"Pending process {process_id} started (size {size}, lifetime {lifetime}s)", "success")
                        self._schedule_auto_removal(process_id, lifetime)
                    else:
                        self._log_message(f"Failed to start pending process {process_id}", "error")
                self.pending_processes.clear()  # Clear pending queue after allocation

            if self.auto_generate_processes:
                self.simulation_thread = threading.Thread(target=self._run_simulation)
                self.simulation_thread.daemon = True
                self.simulation_thread.start()


    
    def _run_simulation(self):
        """This method only runs if auto-generate processes is enabled"""
        self._log_message("Auto-generating processes...", "info")
        while self.simulation_running and self.auto_generate_processes:
            # Add random process only if auto-generate is enabled
            self._add_random_process()
            time.sleep(self.simulation_speed)
    

    def _add_process(self):
        try:
            size = int(self.process_size_var.get())
            if size <= 0:
                self._log_message("Process size must be positive", "error")
                return

            # Check process ID
            if self.process_id_var.get():
                process_id = int(self.process_id_var.get())
                # Check if process ID is already in use
                if process_id in self.allocated_process_ids:
                    self._log_message(f"Process ID {process_id} is already in use", "error")
                    return
            else:
                # Generate a unique process ID
                process_id = self._generate_unique_process_id()

            method_str = self.allocation_method_var.get()
            method = AllocationMethod.PAGING if method_str == "paging" else AllocationMethod.SEGMENTATION

            # Read lifetime for this process
            lifetime = float(self.process_lifetime_var.get())
            
            if self.simulation_running:
                success = self.memory_manager.allocate_process(process_id, size, method)
                if success:
                    # Add process ID to allocated set
                    self.allocated_process_ids.add(process_id)
                    self._log_message(f"Process {process_id} added (size {size}, lifetime {lifetime}s)", "success")
                    self._schedule_auto_removal(process_id, lifetime)
                else:
                    self._log_message(f"Failed to allocate process {process_id}", "error")
            else:
                if not hasattr(self, 'pending_processes'):
                    self.pending_processes = []
                
                # Check for duplicate process ID in pending queue
                if any(process[0] == process_id for process in self.pending_processes):
                    self._log_message(f"Process ID {process_id} is already in pending queue", "error")
                    return
                
                self.pending_processes.append((process_id, size, method, lifetime))
                self._log_message(f"Process {process_id} added to pending queue (size {size}, lifetime {lifetime}s)", "info")

        except ValueError:
            self._log_message("Invalid input values", "error")

    def _generate_unique_process_id(self):
        """Generate a unique process ID"""
        while True:
            process_id = self.process_generator.next_pid
            self.process_generator.next_pid += 1
            
            # Check if ID is not in current allocated processes or pending processes
            if process_id not in self.allocated_process_ids:
                if not hasattr(self, 'pending_processes') or \
                   not any(pending_process[0] == process_id for pending_process in self.pending_processes):
                    return process_id
    
    def _add_random_process(self):
        if not self.simulation_running:
            self._log_message("Start simulation before adding processes", "error")
            return
            
        process_id, size = self.process_generator.generate_process()
        method_str = self.allocation_method_var.get()
        method = AllocationMethod.PAGING if method_str == "paging" else AllocationMethod.SEGMENTATION
        success = self.memory_manager.allocate_process(process_id, size, method)
        if success:
            self._log_message(f"Added random process {process_id} with size {size}", "success")
            self._schedule_auto_removal(process_id)
        else:
            self._log_message(f"Failed to allocate random process {process_id} with size {size}", "error")
    
    def _remove_process(self):
        if not self.simulation_running:
            self._log_message("Start simulation before removing processes", "error")
            return
            
        try:
            process_id = int(self.process_id_var.get())
            success = self.memory_manager.deallocate_process(process_id)
            if success:
                # Remove process ID from allocated set
                self.allocated_process_ids.discard(process_id)
                self._log_message(f"Removed process {process_id}", "success")
            else:
                self._log_message(f"Failed to remove process {process_id}", "error")
        except ValueError:
            self._log_message("Invalid process ID", "error")
    
    def _apply_settings(self):
        try:
            new_memory_size = int(self.memory_size_var.get())
            new_page_size = int(self.page_size_var.get())
            if new_memory_size <= 0 or new_page_size <= 0:
                self._log_message("Memory size and page size must be positive", "error")
                return
            if new_memory_size % new_page_size != 0:
                self._log_message("Memory size must be a multiple of page size", "error")
                return
            self.memory_size = new_memory_size
            self.page_size = new_page_size
            self._reset_simulation()
            self._log_message(f"Applied new settings: Memory size={new_memory_size}, Page size={new_page_size}", "info")
        except ValueError:
            self._log_message("Invalid memory or page size", "error")
    
    def _reset_simulation(self):
        if self.simulation_running:
            self._toggle_simulation()
        self.memory_manager = MemoryManager(self.memory_size, self.page_size)
        self.process_generator.next_pid = 1
        # Clear the set of allocated process IDs
        self.allocated_process_ids.clear()
        self._log_message("Simulation reset", "info")
    
    def _schedule_auto_removal(self, process_id, lifetime):
        timer = threading.Timer(lifetime, self._auto_remove_process, args=(process_id,))
        timer.daemon = True
        timer.start()

    
    def _auto_remove_process(self, process_id):
        # Only try to remove if simulation is still running
        if self.simulation_running:
            removed = self.memory_manager.deallocate_process(process_id)
            if removed:
                # Remove process ID from allocated set
                self.allocated_process_ids.discard(process_id)
                self._log_message(f"Automatically removed process {process_id} after lifetime expiration", "info")
            else:
                self._log_message(f"Failed to auto-remove process {process_id}", "error")

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryVisualizerGUI(root)
    root.mainloop()