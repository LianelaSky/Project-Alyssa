class CharacterMemory:
    def __init__(self):
        self.character_name = "Poppy"
        self.personality = "Arrogant, popular, snarky. Thinks she's better than everyone. Hides vulnerability under a confident mask."
        self.relationship_with_user = "Reluctant partner. Mild rivalry. Secret curiosity."
        self.base_history = """Poppy is a 21-year-old college student, known as the queen of the school..."""
        self.dynamic_history = """Poppy's internal conflict is growing..."""

    def evolve_history(self, new_event):
        self.dynamic_history += f" {new_event}"

    def update_relationship(self, new_relationship):
        self.relationship_with_user = new_relationship

    def get_character_info(self):
        return {
            "name": self.character_name,
            "personality": self.personality,
            "relationship_with_user": self.relationship_with_user,
            "base_history": self.base_history,
            "dynamic_history": self.dynamic_history
        }

class UserMemory:
    def __init__(self):
        self.user_name = "Lia"
        self.age = 20
        self.personality = "Reserved but recently becoming more extroverted."
        self.relationship_with_character = "Neutral. No particular bond yet."
        self.history = """Lia is a 20-year-old student who's always been reserved..."""
        self.memories = []

    def update_relationship(self, relationship_status):
        self.relationship_with_character = relationship_status
        self.memories.append(f"Relationship with Poppy changed to '{relationship_status}'.")

    def add_memory(self, memory):
        self.memories.append(memory)

    def get_user_info(self):
        return {
            "name": self.user_name,
            "personality": self.personality,
            "relationship_with_character": self.relationship_with_character,
            "recent_memories": " | ".join(self.memories[-3:])
        }