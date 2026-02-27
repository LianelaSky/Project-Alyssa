# dynamic_memory.py
import logging

# Get a logger specific to this module, inheriting from 'memory'
# This ensures its messages go to memory_log_handler (if configured)
logger = logging.getLogger('memory.dynamic')

class DynamicMemory:
    def __init__(self):
        self.location = "Science class" # Initial location
        self.current_action = "Waiting before the project discussion" # Initial action
        self.last_narrative_action = "*Is waiting impatiently.*" # Initial narrative action state
        self.memories = [] # Stores recent conversation turns/events
        self.max_events = 3  # How many turns to keep in dynamic memory
        self.relevance_keywords = ["hug", "tears", "sorry", "together", "project", "conflict", "emotion", "fault", "explain", "antidepressants", "anxiety", "house", "library", "fail", "die", "death", "kill"] # Expanded list
        logger.debug("DynamicMemory initialized. Location: %s, Action: %s, Last Narrative: %s", self.location, self.current_action, self.last_narrative_action)

    def add_memory(self, memory, active_memory):
        """Adds a memory event. Relevant new events are immediately proposed
           to active memory. Older events might be dropped upon capacity limit."""
        logger.debug("--- DynamicMemory: add_memory called ---")
        logger.debug("Input memory: '%s...'", memory[:100])
        logger.debug("Current dynamic memory state (before add): %s", self.memories)

        is_new_memory_relevant = self._is_relevant(memory)
        logger.debug("Is new memory relevant? %s", is_new_memory_relevant)
        memory_already_in_active = any(memory == m for m in active_memory.memories)
        logger.debug("Is memory already in active? %s", memory_already_in_active)

        # 1. Add the new event to dynamic memory
        self.memories.append(memory)
        log_msg_info = f"Added to dynamic: '{memory[:70]}...'" # Summary for INFO level
        logger.debug("Dynamic memory state (after add): %s", self.memories) # Detailed content

        # 2. If the NEW event is relevant AND not already in active, add it immediately
        if is_new_memory_relevant and not memory_already_in_active:
            logger.debug("Proposing relevant memory to active: '%s...'", memory[:70])
            active_memory.add_memory(memory) # Let ActiveMemory handle its own logging
            log_msg_info += " | Proposed relevant to active."
        elif is_new_memory_relevant and memory_already_in_active:
             log_msg_info += " | Relevant but already in active."
             logger.debug("Relevant memory already present in active memory, not re-adding.")


        # 3. Handle capacity limit: simply remove the oldest if exceeded
        if len(self.memories) > self.max_events:
            oldest_memory = self.memories.pop(0)
            log_msg_info += f" | Popped oldest due to capacity: '{oldest_memory[:70]}...'"
            logger.debug("Popped oldest memory: '%s...'", oldest_memory[:100])
            logger.debug("Dynamic memory state (after pop): %s", self.memories) # Detailed content

        logger.info(log_msg_info) # Log the summary message at INFO level
        logger.debug("--- DynamicMemory: add_memory finished ---")

    def _is_relevant(self, memory):
        """Check if a memory is relevant based on keywords."""
        memory_lower = memory.lower()
        is_rel = any(keyword in memory_lower for keyword in self.relevance_keywords)
        logger.debug("Relevance check for '%s...': %s", memory[:50], is_rel)
        return is_rel

    def set_last_narrative_action(self, action_text):
        """Stores the latest narrative action performed by the character."""
        if isinstance(action_text, str) and action_text.strip():
            old_action = self.last_narrative_action
            self.last_narrative_action = action_text.strip()
            logger.debug("Updated last_narrative_action from '%s' to '%s'", old_action, self.last_narrative_action)
        else:
            logger.warning("Attempted to set invalid last_narrative_action: %s", action_text)

    def update_location(self, location, active_memory):
        """Updates the current location. Called AFTER the turn by logic.py."""
        if self.location != location:
            logger.info("Dynamic location updating from '%s' to '%s'", self.location, location) # Keep INFO for state change
            self.location = location
        else:
            logger.debug("update_location called but location unchanged: %s", location)


    def update_action(self, action, active_memory):
        """Updates the current general action/task. Called AFTER the turn by logic.py."""
        if self.current_action != action:
            logger.info("Dynamic current_action updating from '%s' to '%s'", self.current_action, action) # Keep INFO for state change
            self.current_action = action
        else:
             logger.debug("update_action called but action unchanged: %s", action)

    def current_state(self):
        """Returns the current state for context building (excluding last narrative action)."""
        state = {
            "location": self.location,
            "action": self.current_action, # The general task/situation action
            "recent_memories": " | ".join(self.memories) if self.memories else ""
        }
        logger.debug("Returning current dynamic state: %s", state)
        return state
