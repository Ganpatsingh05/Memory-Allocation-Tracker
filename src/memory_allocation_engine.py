from enum import Enum, auto
import time
from typing import Dict, List, Optional, Tuple
import random
# Define the AllocationMethod enum
class AllocationMethod(Enum):
    PAGING = auto()
    SEGMENTATION = auto()

# Memory Manager class
class MemoryManager:

    def __init__(self, memory_size, page_size):
        self.memory_size = memory_size
        self.page_size = page_size
        self.memory = [{'start': 0, 'end': memory_size - 1, 'size': memory_size, 'process_id': None}]
        self.page_table = [{'frame_id': i, 'process_id': None, 'start_address': i * page_size, 
                           'end_address': (i + 1) * page_size - 1} 
                          for i in range(memory_size // page_size)]
        self.allocated_processes = {}
        self.recent_events = []
        self.stats = {
            'total_memory': memory_size,
            'used_memory': 0,
            'free_memory': memory_size,
            'used_percentage': 0,
            'process_count': 0,
            'page_faults': 0,
            'external_fragmentation': 0,
            'internal_fragmentation': 0
        }
    
    def get_memory_snapshot(self):
        return self.memory.copy()
    
    def get_page_table_snapshot(self):
        return self.page_table.copy()
    
    def get_memory_stats(self):
        return self.stats.copy()
    
    def get_recent_events(self):
        return self.recent_events[-5:] if self.recent_events else []
    
    def allocate_process(self, process_id, size, method):
        if method == AllocationMethod.PAGING:
            return self._allocate_process_paging(process_id, size)
        else:
            return self._allocate_process_segmentation(process_id, size)
    
    def _allocate_process_paging(self, process_id, size):
        pages_needed = (size + self.page_size - 1) // self.page_size
        free_frames = [frame for frame in self.page_table if frame['process_id'] is None]
        
        if len(free_frames) < pages_needed:
            self._log_event(process_id, "Allocation Failed", f"Not enough free frames. Needed {pages_needed}, available {len(free_frames)}")
            return False
        
        allocated_frames = free_frames[:pages_needed]
        for frame in allocated_frames:
            frame['process_id'] = process_id
        
        self._update_memory_from_page_table()
        self.allocated_processes[process_id] = {
            'size': size,
            'frames': [frame['frame_id'] for frame in allocated_frames],
            'method': 'paging'
        }
        self._update_stats()
        self._log_event(process_id, "Allocation", f"Allocated {pages_needed} pages for size {size}")
        return True
    
    def _allocate_process_segmentation(self, process_id, size):
        for i, block in enumerate(self.memory):
            if block['process_id'] is None and block['size'] >= size:
                if block['size'] == size:
                    block['process_id'] = process_id
                else:
                    end_addr = block['start'] + size - 1
                    new_block = {
                        'start': block['start'] + size,
                        'end': block['end'],
                        'size': block['size'] - size,
                        'process_id': None
                    }
                    block['end'] = end_addr
                    block['size'] = size
                    block['process_id'] = process_id
                    self.memory.insert(i + 1, new_block)
                
                start_page = block['start'] // self.page_size
                end_page = block['end'] // self.page_size
                for frame in self.page_table:
                    if start_page <= frame['frame_id'] <= end_page:
                        frame['process_id'] = process_id
                
                self.allocated_processes[process_id] = {
                    'size': size,
                    'start': block['start'],
                    'end': block['end'],
                    'method': 'segmentation'
                }
                self._update_stats()
                self._log_event(process_id, "Allocation", f"Allocated segment of size {size} at address {block['start']}")
                return True
        
        self._log_event(process_id, "Allocation Failed", f"No suitable free block found for size {size}")
        return False
    
    def deallocate_process(self, process_id):
        if process_id not in self.allocated_processes:
            return False
        
        process_info = self.allocated_processes[process_id]
        
        if process_info['method'] == 'paging':
            for frame_id in process_info['frames']:
                for frame in self.page_table:
                    if frame['frame_id'] == frame_id:
                        frame['process_id'] = None
            self._update_memory_from_page_table()
        else:
            for block in self.memory:
                if block['process_id'] == process_id:
                    block['process_id'] = None
                    start_page = block['start'] // self.page_size
                    end_page = block['end'] // self.page_size
                    for frame in self.page_table:
                        if start_page <= frame['frame_id'] <= end_page:
                            frame['process_id'] = None
                    break
            self._merge_free_blocks()
        
        del self.allocated_processes[process_id]
        self._update_stats()
        self._log_event(process_id, "Deallocation", "Process removed from memory")
        return True
    
    def _update_memory_from_page_table(self):
        self.memory = []
        current_block = None
        for frame in sorted(self.page_table, key=lambda x: x['frame_id']):
            start_addr = frame['start_address']
            end_addr = frame['end_address']
            process_id = frame['process_id']
            if current_block is None or current_block['process_id'] != process_id:
                if current_block is not None:
                    self.memory.append(current_block)
                current_block = {
                    'start': start_addr,
                    'end': end_addr,
                    'size': end_addr - start_addr + 1,
                    'process_id': process_id
                }
            else:
                current_block['end'] = end_addr
                current_block['size'] = current_block['end'] - current_block['start'] + 1
        if current_block is not None:
            self.memory.append(current_block)
    
    def _merge_free_blocks(self):
        i = 0
        while i < len(self.memory) - 1:
            if self.memory[i]['process_id'] is None and self.memory[i+1]['process_id'] is None:
                self.memory[i]['end'] = self.memory[i+1]['end']
                self.memory[i]['size'] += self.memory[i+1]['size']
                self.memory.pop(i+1)
            else:
                i += 1
    
    def _update_stats(self):
        used_memory = sum(block['size'] for block in self.memory if block['process_id'] is not None)
        free_memory = self.memory_size - used_memory
        free_blocks = [block for block in self.memory if block['process_id'] is None]
        largest_free_block = max([block['size'] for block in free_blocks], default=0)
        external_fragmentation = 0
        if free_memory > 0:
            external_fragmentation = 1 - (largest_free_block / free_memory)
        
        internal_fragmentation = 0
        for process_id, info in self.allocated_processes.items():
            if info['method'] == 'paging':
                allocated_size = len(info['frames']) * self.page_size
                internal_fragmentation += allocated_size - info['size']
        
        self.stats = {
            'total_memory': self.memory_size,
            'used_memory': used_memory,
            'free_memory': free_memory,
            'used_percentage': (used_memory / self.memory_size) * 100 if self.memory_size > 0 else 0,
            'process_count': len(self.allocated_processes),
            'page_faults': 0,
            'external_fragmentation': external_fragmentation,
            'internal_fragmentation': internal_fragmentation
        }
    
    def _log_event(self, process_id, event_type, details):
        event = {
            'timestamp': time.time(),
            'process_id': process_id,
            'event_type': event_type,
            'details': details
        }
        self.recent_events.append(event)
        if len(self.recent_events) > 10:
            self.recent_events.pop(0)
    

# Process Generator
class ProcessGenerator:
    def __init__(self, min_size, max_size):
        self.min_size = min_size
        self.max_size = max_size
        self.next_pid = 1
    
    def generate_process(self):
        process_id = self.next_pid
        self.next_pid += 1
        size = random.randint(self.min_size, self.max_size)
        return process_id, size
    
