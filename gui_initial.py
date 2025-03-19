# gui.py

import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import time
import random
from typing import Dict, List, Optional, Tuple

# Import from our modules
from memory_allocation_engine import MemoryManager, ProcessGenerator, AllocationMethod
from visualization import MemoryVisualizer

class MemoryVisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Memory Allocation Visualizer")
        self.root.geometry("1200x800")
        
        # Set up the memory manager and visualizer
        self.memory_size = 256
        self.page_size = 16
        self.memory_manager = MemoryManager(self.memory_size, self.page_size)
        self.visualizer = MemoryVisualizer()
        self.process_generator = ProcessGenerator(4, 64)
        
        # Default allocation method
        self.allocation_method = AllocationMethod.PAGING
        
        # Simulation control
        self.simulation_running = False
        self.simulation_thread = None
        self.simulation_speed = 1.0  # seconds between actions
        
        # Create the GUI elements
        self._create_control_panel()
        self._create_process_panel()
        self._create_log_panel()
        
        # Start the update loop
        self._update_visualization()

    def _create_control_panel(self):
        control_frame = ttk.LabelFrame(self.root, text="Simulation Controls")
        control_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nw")
        
        # Memory size control
        ttk.Label(control_frame, text="Memory Size:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.memory_size_var = tk.StringVar(value=str(self.memory_size))
        memory_size_entry = ttk.Entry(control_frame, width=10, textvariable=self.memory_size_var)
        memory_size_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Page size control
        ttk.Label(control_frame, text="Page Size:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_entry = ttk.Entry(control_frame, width=10, textvariable=self.page_size_var)
        page_size_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Allocation method control
        ttk.Label(control_frame, text="Allocation Method:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.allocation_method_var = tk.StringVar(value="paging")
        allocation_method_combo = ttk.Combobox(control_frame, textvariable=self.allocation_method_var, 
                                              values=["paging", "segmentation"], state="readonly", width=12)
        allocation_method_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Simulation speed control
        ttk.Label(control_frame, text="Simulation Speed:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(control_frame, from_=0.1, to=3.0, orient=tk.HORIZONTAL, 
                               variable=self.speed_var, length=100)
        speed_scale.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        
        # Reset button
        reset_button = ttk.Button(control_frame, text="Reset", command=self._reset_simulation)
        reset_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")
        
        # Apply settings button
        apply_button = ttk.Button(control_frame, text="Apply Settings", command=self._apply_settings)
        apply_button.grid(row=4, column=1, padx=5, pady=5, sticky="w")
        
        # Start/Stop button
        self.start_stop_var = tk.StringVar(value="Start Simulation")
        self.start_stop_button = ttk.Button(control_frame, textvariable=self.start_stop_var, 
                                           command=self._toggle_simulation)
        self.start_stop_button.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="we")

    def _create_process_panel(self):
        process_frame = ttk.LabelFrame(self.root, text="Process Management")
        process_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nw")
        
        # Process size control
        ttk.Label(process_frame, text="Process Size:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.process_size_var = tk.StringVar(value="32")
        process_size_entry = ttk.Entry(process_frame, width=10, textvariable=self.process_size_var)
        process_size_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Add process button
        add_process_button = ttk.Button(process_frame, text="Add Process", command=self._add_process)
        add_process_button.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        
        # Remove process control
        ttk.Label(process_frame, text="Process ID:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.process_id_var = tk.StringVar()
        process_id_entry = ttk.Entry(process_frame, width=10, textvariable=self.process_id_var)
        process_id_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Remove process button
        remove_process_button = ttk.Button(process_frame, text="Remove Process", command=self._remove_process)
        remove_process_button.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        
        # Add random process button
        random_process_button = ttk.Button(process_frame, text="Add Random Process", command=self._add_random_process)
        random_process_button.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky="we")

    def _create_log_panel(self):
        log_frame = ttk.LabelFrame(self.root, text="Event Log")
        log_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=40, height=10)
        self.log_text.grid(row=0, column=0, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)

    def _update_visualization(self):
        try:
            # Get the current snapshots
            memory_snapshot = self.memory_manager.get_memory_snapshot()
            page_table_snapshot = self.memory_manager.get_page_table_snapshot()
            stats = self.memory_manager.get_memory_stats()
            events = self.memory_manager.get_recent_events(10)
            
            # Update the visualization
            self.visualizer.update_visualization(
                memory_snapshot,
                page_table_snapshot,
                stats,
                events,
                self.memory_size,
                self.page_size,
                self.allocation_method_var.get()
            )
            
            # Update the log
            self._update_log(events)
            
            # Schedule the next update
            self.root.after(100, self._update_visualization)
        except Exception as e:
            print(f"Error updating visualization: {e}")

    def _update_log(self, events):
        # Update the log text box with the most recent events
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for event in events:
            timestamp = time.strftime('%H:%M:%S', time.localtime(event['timestamp']))
            log_entry = f"{timestamp} - {event['event_type']}: P{event['process_id']} - {event['details']}\n"
            self.log_text.insert(tk.END, log_entry)
        
        self.log_text.config(state=tk.DISABLED)

    def _toggle_simulation(self):
        if self.simulation_running:
            self._stop_simulation()
        else:
            self._start_simulation()

    def _start_simulation(self):
        self.simulation_running = True
        self.start_stop_var.set("Stop Simulation")
        self.simulation_thread = threading.Thread(target=self._simulation_loop)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()

    def _stop_simulation(self):
        self.simulation_running = False
        self.start_stop_var.set("Start Simulation")
        if self.simulation_thread:
            self.simulation_thread.join(timeout=1.0)
            self.simulation_thread = None

    def _simulation_loop(self):
        while self.simulation_running:
            # Get the current speed
            speed = self.speed_var.get()
            
            # Randomly decide whether to add or remove a process
            if random.random() < 0.7:  # 70% chance to add
                self._add_random_process()
            else:  # 30% chance to remove
                # Get the list of active processes
                active_processes = list(self.memory_manager.processes.keys())
                if active_processes:
                    process_id = random.choice(active_processes)
                    self._remove_specific_process(process_id)
            
            # Sleep for the specified simulation speed
            time.sleep(3.0 / speed)  # Inverse relationship: higher speed = less wait time

    def _add_process(self):
        try:
            # Get the process size from the entry
            size = int(self.process_size_var.get())
            
            # Get the next process ID
            process_id = self.process_generator.next_pid
            self.process_generator.next_pid += 1
            
            # Choose allocation method
            method = AllocationMethod.PAGING if self.allocation_method_var.get() == "paging" else AllocationMethod.SEGMENTATION
            
            # Allocate the process
            success = self.memory_manager.allocate_process(process_id, size, method)
            
            # Log the result
            if success:
                print(f"Process {process_id} allocated successfully")
            else:
                print(f"Failed to allocate process {process_id}")
        except ValueError:
            print("Please enter a valid process size")

    def _add_random_process(self):
        # Generate a random process
        process_id, size = self.process_generator.generate_process()
        
        # Choose allocation method
        method = AllocationMethod.PAGING if self.allocation_method_var.get() == "paging" else AllocationMethod.SEGMENTATION
        
        # Allocate the process
        self.memory_manager.allocate_process(process_id, size, method)

    def _remove_process(self):
        try:
            # Get the process ID from the entry
            process_id = int(self.process_id_var.get())
            
            # Remove the process
            self._remove_specific_process(process_id)
        except ValueError:
            print("Please enter a valid process ID")

    def _remove_specific_process(self, process_id):
        # Deallocate the process
        success = self.memory_manager.deallocate_process(process_id)
        
        # Log the result
        if success:
            print(f"Process {process_id} deallocated successfully")
        else:
            print(f"Failed to deallocate process {process_id}")

    def _reset_simulation(self):
        # Stop the simulation if it's running
        if self.simulation_running:
            self._stop_simulation()
        
        # Reset the memory manager
        self._apply_settings()
        
        # Clear the log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _apply_settings(self):
        try:
            # Get the memory size and page size
            memory_size = int(self.memory_size_var.get())
            page_size = int(self.page_size_var.get())
            
            # Validate the settings
            if memory_size <= 0 or page_size <= 0 or memory_size % page_size != 0:
                raise ValueError("Invalid memory size or page size")
            
            # Create a new memory manager
            self.memory_size = memory_size
            self.page_size = page_size
            self.memory_manager = MemoryManager(memory_size, page_size)
            
            # Update the allocation method
            self.allocation_method = AllocationMethod.PAGING if self.allocation_method_var.get() == "paging" else AllocationMethod.SEGMENTATION
            
            print(f"Settings applied: Memory size = {memory_size}, Page size = {page_size}, Method = {self.allocation_method.value}")
        except ValueError as e:
            print(f"Error applying settings: {e}")

def main():
    root = tk.Tk()
    app = MemoryVisualizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()