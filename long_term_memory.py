# long_term_memory.py
import logging

# Get a logger specific to this module, inheriting from 'memory'
logger = logging.getLogger('memory.longterm')

class LongTermMemoryFile:
    def __init__(self):
        self.memory = []
        logger.debug("LongTermMemoryFile initialized.")

    def add_event(self, event):
        """Adds a summarized event (usually from ActiveMemory) to long-term memory."""
        logger.debug("--- LongTermMemory: add_event called ---")
        logger.debug("Event to add: '%s...'", event[:100])
        # Avoid adding exact duplicates? Optional.
        # if event not in self.memory:
        self.memory.append(event)
        logger.info("Added event summary to Long Term Memory. Total LTM size: %d", len(self.memory))
        logger.debug("LTM content (last item): %s", self.memory[-1])
        # else:
        #     logger.debug("Skipped adding duplicate event to LTM.")
        logger.debug("--- LongTermMemory: add_event finished ---")


    def get_memories(self):
        """Returns all memories stored in long-term memory."""
        logger.debug("Getting all %d long-term memories.", len(self.memory))
        # Avoid logging all LTM if it gets large
        logger.debug("LTM content sample (last 2): %s", self.memory[-2:])
        return self.memory

    def clear_memory(self):
        """Clears all long-term memory."""
        logger.warning("Clearing ALL (%d) long-term memories!", len(self.memory)) # Warning level seems appropriate
        self.memory = []
