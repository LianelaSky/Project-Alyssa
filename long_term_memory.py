# long_term_memory.py
import json
import logging
import os

# Get a logger specific to this module, inheriting from 'memory'
logger = logging.getLogger('memory.longterm')


class LongTermMemoryFile:
    def __init__(self, storage_file="long_term_memory.json"):
        self.storage_file = storage_file
        self.memory = []
        self._load()
        logger.debug("LongTermMemoryFile initialized with %d events.", len(self.memory))

    def _load(self):
        if not os.path.exists(self.storage_file):
            return
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                self.memory = data
            else:
                logger.warning("Invalid long-term memory format in %s. Resetting.", self.storage_file)
                self.memory = []
        except (IOError, json.JSONDecodeError) as exc:
            logger.error("Failed to load long-term memory from %s: %s", self.storage_file, exc, exc_info=True)
            self.memory = []

    def _save(self):
        tmp = self.storage_file + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.storage_file)
        except IOError as exc:
            logger.error("Failed to save long-term memory to %s: %s", self.storage_file, exc, exc_info=True)
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass

    def add_event(self, event):
        """Adds a summarized event (usually from ActiveMemory) to long-term memory."""
        logger.debug("--- LongTermMemory: add_event called ---")
        if not isinstance(event, str) or not event.strip():
            logger.warning("Ignored invalid long-term memory event: %s", event)
            return
        event = event.strip()
        if self.memory and self.memory[-1] == event:
            logger.debug("Skipped consecutive duplicate long-term memory event.")
            return
        self.memory.append(event)
        logger.info("Added event summary to Long Term Memory. Total LTM size: %d", len(self.memory))
        self._save()
        logger.debug("--- LongTermMemory: add_event finished ---")

    def get_memories(self):
        """Returns all memories stored in long-term memory."""
        logger.debug("Getting all %d long-term memories.", len(self.memory))
        return list(self.memory)

    def clear_memory(self):
        """Clears all long-term memory."""
        logger.warning("Clearing ALL (%d) long-term memories!", len(self.memory))
        self.memory = []
        self._save()
