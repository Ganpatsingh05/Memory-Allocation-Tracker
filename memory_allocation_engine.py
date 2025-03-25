# memory_allocation_engine.py

import random
import time
from enum import Enum
from typing import Dict, List, Optional, Tuple

class AllocationMethod(Enum):
    PAGING = "paging"
    SEGMENTATION = "segmentation"

class MemoryBlock:
    def __init__(self, start: int, size: int, process_id: Optional[int] = None):
        self.start = start
        self.size = size
        self.process_id = process_id  # None means free block
        self.allocated_time = time.time() if process_id is not None else None

    @property
    def end(self) -> int:
        return self.start + self.size - 1

    @property
    def is_free(self) -> bool:
        return self.process_id is None

class Page:
    def __init__(self, page_id: int, frame_id: Optional[int] = None):
        self.page_id = page_id
        self.frame_id = frame_id  # None means page is not in memory

class Process:
    def __init__(self, process_id: int, size: int):
        self.process_id = process_id
        self.size = size
        self.pages: List[Page] = []
        self.segments: List[MemoryBlock] = []
        self.allocation_time = time.time()

class MemoryEvent:
    def __init__(self, event_type: str, process_id: int, details: str):
        self.event_type = event_type
        self.process_id = process_id
        self.details = details
        self.timestamp = time.time()

class MemoryManager:
    def __init__(self, total_memory_size: int, page_size: int = 4):
        self.total_memory_size = total_memory_size
        self.page_size = page_size
        self.total_frames = total_memory_size // page_size
        
        # Initialize memory as one large free block
        self.memory_blocks = [MemoryBlock(0, total_memory_size)]
        
        # Page table (frame_id -> process_id)
        self.page_table = [None] * self.total_frames
        
        # Track processes
        self.processes: Dict[int, Process] = {}
        
        # Event log
        self.events: List[MemoryEvent] = []
        
        # Statistics
        self.page_faults = 0
        self.external_fragmentation = 0
        self.internal_fragmentation = 0

    def log_event(self, event_type: str, process_id: int, details: str):
        event = MemoryEvent(event_type, process_id, details)
        self.events.append(event)
        return event

    def allocate_process(self, process_id: int, size: int, method: AllocationMethod) -> bool:
        if process_id in self.processes:
            self.log_event("ERROR", process_id, "Process already exists")
            return False
        
        process = Process(process_id, size)
        self.processes[process_id] = process
        
        if method == AllocationMethod.PAGING:
            return self._allocate_paging(process)
        else:
            return self._allocate_segmentation(process)

    def _allocate_paging(self, process: Process) -> bool:
        num_pages_needed = (process.size + self.page_size - 1) // self.page_size
        
        # Find free frames
        free_frames = [i for i, p in enumerate(self.page_table) if p is None]
        
        if len(free_frames) < num_pages_needed:
            self.log_event("PAGE_FAULT", process.process_id, 
                          f"Not enough free frames. Needed: {num_pages_needed}, Available: {len(free_frames)}")
            self.page_faults += 1
            return False
        
        # Allocate pages to frames
        for i in range(num_pages_needed):
            page = Page(i, free_frames[i])
            process.pages.append(page)
            self.page_table[free_frames[i]] = process.process_id
            
            # Update memory blocks representation
            frame_start = free_frames[i] * self.page_size
            new_block = MemoryBlock(frame_start, self.page_size, process.process_id)
            
            # Find and update the appropriate memory block
            for j, block in enumerate(self.memory_blocks):
                if block.is_free and block.start <= frame_start and block.end >= frame_start + self.page_size - 1:
                    # Split the block
                    self._split_block_for_page(j, frame_start, self.page_size, process.process_id)
                    break
        
        # Calculate internal fragmentation
        last_page_size = process.size % self.page_size
        if last_page_size > 0:
            self.internal_fragmentation += self.page_size - last_page_size
        
        self.log_event("ALLOCATION", process.process_id, 
                      f"Allocated {num_pages_needed} pages for process {process.process_id}")
        return True

    def _split_block_for_page(self, block_idx: int, frame_start: int, page_size: int, process_id: int):
        block = self.memory_blocks[block_idx]
        
        # Check if the block starts before the frame
        if block.start < frame_start:
            # Create a free block before the frame
            pre_block = MemoryBlock(block.start, frame_start - block.start)
            self.memory_blocks.insert(block_idx, pre_block)
            block_idx += 1
        
        # Create the allocated block
        allocated_block = MemoryBlock(frame_start, page_size, process_id)
        
        # Check if there's space after the allocation
        if block.end > frame_start + page_size - 1:
            # Create a free block after the frame
            post_start = frame_start + page_size
            post_size = block.end - post_start + 1
            post_block = MemoryBlock(post_start, post_size)
            
            # Replace the original block with the allocated block and add the post block
            self.memory_blocks[block_idx] = allocated_block
            self.memory_blocks.insert(block_idx + 1, post_block)
        else:
            # Replace the original block with just the allocated block
            self.memory_blocks[block_idx] = allocated_block

    def _allocate_segmentation(self, process: Process) -> bool:
        # Find a suitable free block using first-fit
        suitable_block_idx = None
        
        for i, block in enumerate(self.memory_blocks):
            if block.is_free and block.size >= process.size:
                suitable_block_idx = i
                break
        
        if suitable_block_idx is None:
            self.log_event("ERROR", process.process_id, 
                          f"No suitable free block found for process {process.process_id} (size: {process.size})")
            self._calculate_external_fragmentation()
            return False
        
        # Allocate the segment
        block = self.memory_blocks[suitable_block_idx]
        
        # Create a segment for the process
        segment = MemoryBlock(block.start, process.size, process.process_id)
        process.segments.append(segment)
        
        # Split the block if necessary
        if block.size > process.size:
            # Create a new free block for the remainder
            remainder = MemoryBlock(block.start + process.size, block.size - process.size)
            self.memory_blocks[suitable_block_idx] = segment
            self.memory_blocks.insert(suitable_block_idx + 1, remainder)
        else:
            # Use the entire block
            self.memory_blocks[suitable_block_idx] = segment
        
        self.log_event("ALLOCATION", process.process_id, 
                      f"Allocated segment for process {process.process_id} at address {segment.start}")
        return True

    def deallocate_process(self, process_id: int) -> bool:
        if process_id not in self.processes:
            self.log_event("ERROR", process_id, "Process not found")
            return False
        
        process = self.processes[process_id]
        
        if process.pages:  # Paging
            self._deallocate_paging(process)
        elif process.segments:  # Segmentation
            self._deallocate_segmentation(process)
        
        del self.processes[process_id]
        self.log_event("DEALLOCATION", process_id, f"Deallocated process {process_id}")
        return True

    def _deallocate_paging(self, process: Process):
        # Free frames in page table
        for page in process.pages:
            if page.frame_id is not None:
                self.page_table[page.frame_id] = None
        
        # Update memory blocks
        for i, block in enumerate(self.memory_blocks[:]):
            if block.process_id == process.process_id:
                self.memory_blocks[i] = MemoryBlock(block.start, block.size)
        
        # Merge adjacent free blocks
        self._merge_adjacent_free_blocks()

    def _deallocate_segmentation(self, process: Process):
        # Update memory blocks
        for segment in process.segments:
            for i, block in enumerate(self.memory_blocks):
                if block.start == segment.start and block.process_id == process.process_id:
                    self.memory_blocks[i] = MemoryBlock(block.start, block.size)
                    break
        
        # Merge adjacent free blocks
        self._merge_adjacent_free_blocks()

    def _merge_adjacent_free_blocks(self):
        i = 0
        while i < len(self.memory_blocks) - 1:
            current = self.memory_blocks[i]
            next_block = self.memory_blocks[i + 1]
            
            if current.is_free and next_block.is_free:
                # Merge blocks
                merged = MemoryBlock(current.start, current.size + next_block.size)
                self.memory_blocks[i] = merged
                self.memory_blocks.pop(i + 1)
            else:
                i += 1

    def _calculate_external_fragmentation(self):
        total_free = sum(block.size for block in self.memory_blocks if block.is_free)
        largest_free = max((block.size for block in self.memory_blocks if block.is_free), default=0)
        
        if total_free > 0:
            self.external_fragmentation = 1 - (largest_free / total_free)
        else:
            self.external_fragmentation = 0

    def get_memory_snapshot(self) -> List[Dict]:
        snapshot = []
        for block in self.memory_blocks:
            snapshot.append({
                'start': block.start,
                'end': block.end,
                'size': block.size,
                'process_id': block.process_id,
                'is_free': block.is_free
            })
        return snapshot

    def get_page_table_snapshot(self) -> List[Dict]:
        snapshot = []
        for frame_id, process_id in enumerate(self.page_table):
            snapshot.append({
                'frame_id': frame_id,
                'process_id': process_id,
                'start_address': frame_id * self.page_size,
                'end_address': (frame_id + 1) * self.page_size - 1
            })
        return snapshot

    def get_process_info(self, process_id: int) -> Dict:
        if process_id not in self.processes:
            return {}
        
        process = self.processes[process_id]
        return {
            'process_id': process.process_id,
            'size': process.size,
            'pages': [{'page_id': p.page_id, 'frame_id': p.frame_id} for p in process.pages],
            'segments': [{'start': s.start, 'size': s.size} for s in process.segments],
            'allocation_time': process.allocation_time
        }

    def get_memory_stats(self) -> Dict:
        used_memory = sum(block.size for block in self.memory_blocks if not block.is_free)
        free_memory = self.total_memory_size - used_memory
        
        return {
            'total_memory': self.total_memory_size,
            'used_memory': used_memory,
            'free_memory': free_memory,
            'used_percentage': (used_memory / self.total_memory_size) * 100,
            'page_faults': self.page_faults,
            'external_fragmentation': self.external_fragmentation,
            'internal_fragmentation': self.internal_fragmentation,
            'process_count': len(self.processes)
        }

    def get_recent_events(self, limit: int = 10) -> List[Dict]:
        events = []
        for event in self.events[-limit:]:
            events.append({
                'event_type': event.event_type,
                'process_id': event.process_id,
                'details': event.details,
                'timestamp': event.timestamp
            })
        return events

class ProcessGenerator:
    def __init__(self, min_size: int = 4, max_size: int = 64):
        self.min_size = min_size
        self.max_size = max_size
        self.next_pid = 1

    def generate_process(self) -> Tuple[int, int]:
        process_id = self.next_pid
        self.next_pid += 1
        size = random.randint(self.min_size, self.max_size)
        return process_id, size
    