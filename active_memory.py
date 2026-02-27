# active_memory.py
from long_term_memory import LongTermMemoryFile
import logging

# Get a logger specific to this module, inheriting from 'memory'
logger = logging.getLogger('memory.active')

class ActiveMemoryFile:
    def __init__(self, threshold=25, summary_size=5):
        self.memories = [] # Active memory buffer
        self.threshold = threshold # Limit to compress to LTM
        self.summary_size = summary_size # How many memories to save to LTM per batch
        self.long_term_file = LongTermMemoryFile() # LTM instance
        self.message_count = 0 # Counter
        self.important_keywords = ["project", "park", "school", "relationship", "conflict", "emotion", "together", "hug", "sorry", "antidepressants", "anxiety", "house", "library", "fault"] # Keywords for LTM compression
        logger.debug("ActiveMemoryFile initialized. Threshold: %d, Summary Size: %d", self.threshold, self.summary_size)

    def add_memory(self, memory):
        """Adds a memory received from dynamic memory (if relevant)."""
        logger.debug("--- ActiveMemory: add_memory called ---")
        logger.debug("Input memory: '%s...'", memory[:100])
        logger.debug("Current active memory state (before add, size %d): %s", len(self.memories), self.memories if len(self.memories) < 10 else "[Too long to log fully]") # Log content only if short

        if memory not in self.memories:
             self.memories.append(memory)
             # Keep INFO log for successful addition summary
             logger.info("Added to active memory: '%s...'", memory[:70])
             logger.debug("Active memory state (after add, size %d): %s", len(self.memories), self.memories if len(self.memories) < 10 else "[Too long to log fully]")
             self.message_count += 1
             logger.debug("Message count incremented to: %d", self.message_count)
             # Check if the threshold for archiving to LTM has been reached
             if len(self.memories) >= self.threshold:
                 logger.info("Active memory threshold (%d) reached. Triggering compression.", self.threshold)
                 self.compress_and_send()
        else:
             logger.debug("Skipped adding duplicate to active memory: '%s...'", memory[:70])
        logger.debug("--- ActiveMemory: add_memory finished ---")


    def compress_and_send(self):
        """Compresses the oldest batch of memories and sends them to LTM."""
        logger.debug("--- ActiveMemory: compress_and_send called ---")
        if len(self.memories) < self.threshold:
             logger.debug("Compress: Batch size %d < threshold %d. Skipping.", len(self.memories), self.threshold)
             logger.debug("--- ActiveMemory: compress_and_send finished (skipped) ---")
             return

        batch_to_process = self.memories[:self.threshold]
        self.memories = self.memories[self.threshold:] # Remove the processed batch

        logger.info("Compress: Processing batch of %d. Remaining active: %d", len(batch_to_process), len(self.memories))
        logger.debug("Batch to process: %s", batch_to_process)
        logger.debug("Active memories after removing batch: %s", self.memories if len(self.memories) < 10 else "[Too long to log fully]")

        # Select important memories from the batch
        important_memories = [m for m in batch_to_process if any(keyword in m.lower() for keyword in self.important_keywords)]
        logger.info("Compress: Found %d important memories in batch.", len(important_memories))
        logger.debug("Important memories found: %s", important_memories)

        # Create the summary for LTM
        compressed_summary_list = []
        if len(important_memories) >= self.summary_size:
            compressed_summary_list = important_memories[:self.summary_size]
            logger.debug("Compress: Using first %d important memories for LTM summary.", self.summary_size)
        else:
            compressed_summary_list = important_memories
            needed = self.summary_size - len(compressed_summary_list)
            if needed > 0:
                recent_non_important = [m for m in reversed(batch_to_process) if m not in compressed_summary_list]
                fill_count = min(needed, len(recent_non_important))
                compressed_summary_list.extend(recent_non_important[:fill_count])
                logger.debug("Compress: Using %d important + %d recent non-important memories for LTM summary.", len(important_memories), fill_count)

        logger.debug("Final summary list for LTM: %s", compressed_summary_list)

        # Join the summary and send it to LTM if not empty
        if compressed_summary_list:
            summary_event = "\n---\n".join(compressed_summary_list) # Use separator
            # Let long_term_file handle its own logging
            self.long_term_file.add_event(summary_event)
            logger.info("Compress: Sent summary of %d items to LTM.", len(compressed_summary_list))
        else:
             logger.info("Compress: No memories selected for LTM summary.")
        logger.debug("--- ActiveMemory: compress_and_send finished ---")


    def get_recent_active_memories(self, count=10):
        """Returns the most recent 'count' memories directly from the active buffer."""
        logger.debug("Getting last %d active memories.", count)
        # Ensure count is not larger than the list size
        actual_count = min(count, len(self.memories))
        mems = self.memories[-actual_count:]
        logger.debug("Returning %d memories: %s", actual_count, mems if actual_count < 5 else "[Too many to log fully]")
        return mems

