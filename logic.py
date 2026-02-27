# logic.py (Explicit State Tracking + RAG + Combined Fatigue/Sleep Logic - Tuned Location Change v2)
import logging
import re # Needed for action extraction
import time
import datetime
import json # Needed for saving/loading state
import os   # Needed for checking if save file exists
import math # Necesario para math.ceil si se usa en tiempo

# Import VectorMemoryStore for RAG
try:
    # Assuming vector_memory.py is in the same directory
    from vector_memory import VectorMemoryStore
except ImportError:
    logging.critical("Failed to import VectorMemoryStore from vector_memory.py. RAG features disabled.")
    VectorMemoryStore = None # Set to None if import fails

# Get loggers
logic_logger = logging.getLogger('logic')
memory_logger = logging.getLogger('memory.logic_interface') # Specific logger for memory actions here

# --- Constantes para el CICLO de Sueño/Vigilia (Controlado por Logic) ---
# (Puedes ajustar estos valores para cambiar el comportamiento)
FATIGUE_THRESHOLD_SLEEP = 75.0 # Nivel de fatiga (leído de EC) para intentar dormir (0-100)
FATIGUE_THRESHOLD_WAKE = 10.0 # Nivel de fatiga (leído de EC) para despertar (0-100)
MIN_SLEEP_HOURS = 6.0 # Mínimo de horas de sueño
MAX_AWAKE_HOURS = 18.0 # Máximo de horas despierto antes de forzar intento de sueño
SLEEP_START_HOUR = 22 # Hora a partir de la cual puede intentar dormir (10 PM)
SLEEP_END_HOUR = 7 # Hora límite para intentar dormir (7 AM)
# --- Fin Constantes Ciclo ---

SAVE_STATE_FILE = "save_state.json" # For general state (time, explicit state, dynamic mem, sleep state)
VECTOR_INDEX_FILE = "memory_index.faiss" # For FAISS index
VECTOR_DATA_FILE = "memory_data.json" # For FAISS data mapping

class RPLogic:
    def __init__(self, character_memory, active_memory, user_memory, emotional_core, dynamic_memory):
        self.character_memory = character_memory
        self.active_memory = active_memory
        self.long_term_memory = None
        self.long_term_memory_legacy = None
        if hasattr(self.active_memory, 'long_term_file') and self.active_memory.long_term_file:
             self.long_term_memory_legacy = self.active_memory.long_term_file

        self.user_memory = user_memory
        self.dynamic_memory = dynamic_memory
        self.emotional_core = emotional_core # Emotional Core handles fatigue level calculation
        self.logger = logic_logger
        self.action_regex = re.compile(r"\*(.*?)\*", re.DOTALL)

        # --- Vector Memory (RAG) Initialization ---
        self.vector_memory = None
        if VectorMemoryStore:
            try:
                self.logger.info("Initializing Vector Memory Store for RAG...")
                self.vector_memory = VectorMemoryStore(model_name='all-MiniLM-L6-v2')
                self.vector_memory.load_memory(index_path=VECTOR_INDEX_FILE, data_path=VECTOR_DATA_FILE)
            except Exception as e:
                self.logger.error(f"Failed to initialize or load VectorMemoryStore: {e}", exc_info=True)
                self.vector_memory = None
        else:
            self.logger.warning("VectorMemoryStore class not available. RAG features will be disabled.")

        # --- Default Initial State ---
        self.current_roleplay_time = datetime.datetime(2025, 4, 16, 14, 0, 0)
        self.last_real_time = time.time()
        self.time_scale_factor = 3 # Usamos el factor 3 que ajustaste
        self.min_time_advance_per_turn = datetime.timedelta(minutes=2)

        # --- Explicit State Variables ---
        self.pending_location_target = None
        self.current_topic_focus = "Initial Setup / Project Discussion"
        self.last_emotional_guidance = {}

        # --- Variables de Estado para CICLO Fatiga/Sueño (Controlado por Logic) ---
        self.hours_awake = 0.0 # Horas continuas despierto
        self.is_sleeping = False # Estado de sueño
        self.hours_slept = 0.0 # Horas continuas dormido
        # --- Fin Variables Ciclo ---

        # --- Time-awareness state ---
        self.location_entered_roleplay_time = self.current_roleplay_time
        self.last_time_awareness_note = ""

        # --- Load General State (overwrites defaults) ---
        self._load_state() # Carga tiempo, estado explícito, memoria dinámica, estado de sueño, etc.

        # Ensure dynamic memory has initial values if not loaded
        if self.dynamic_memory:
            if not hasattr(self.dynamic_memory, 'location') or not self.dynamic_memory.location:
                self.dynamic_memory.location = "Science Class"
            if not hasattr(self.dynamic_memory, 'current_action') or not self.dynamic_memory.current_action:
                 self.dynamic_memory.current_action = "Waiting before the project discussion"
            current_loc = self.dynamic_memory.location
            current_act = self.dynamic_memory.current_action
        else:
            current_loc = "Unknown (DM Error)"
            current_act = "Unknown (DM Error)"
            self.logger.critical("DynamicMemory object not initialized correctly!") # Log critical error

        # Get initial fatigue from Emotional Core for logging
        initial_fatigue = self.emotional_core.fatigue_level if self.emotional_core else "N/A"

        self.logger.info("RPLogic initialized. Location: %s, Action: %s, Topic: %s, Pending Location: %s, RP Time: %s, Sleeping: %s, Fatigue (from EC): %s",
                         current_loc, current_act,
                         self.current_topic_focus, self.pending_location_target,
                         self.current_roleplay_time.strftime("%Y-%m-%d %H:%M:%S"),
                         self.is_sleeping, initial_fatigue)


    def _load_state(self):
        """Loads general state (time, explicit state, dynamic memory, sleep cycle state) from JSON."""
        if os.path.exists(SAVE_STATE_FILE):
            self.logger.info("Save file '%s' found. Attempting to load general state.", SAVE_STATE_FILE)
            try:
                with open(SAVE_STATE_FILE, 'r', encoding='utf-8') as f:
                    state_data = json.load(f)
                self.logger.debug("Loaded raw state data: %s", state_data)

                # Restore Time
                time_str = state_data.get("current_roleplay_time")
                if time_str:
                    try:
                        time_str_clean = time_str.split('+')[0].split('Z')[0].split('.')[0]
                        self.current_roleplay_time = datetime.datetime.fromisoformat(time_str_clean)
                        self.logger.info("Loaded roleplay time: %s", self.current_roleplay_time.strftime("%Y-%m-%d %H:%M:%S"))
                    except ValueError as time_err:
                        self.logger.error("Failed to parse saved roleplay time '%s': %s. Using default.", time_str, time_err)
                        self.current_roleplay_time = datetime.datetime(2025, 4, 16, 14, 0, 0)

                # Restore Dynamic Memory State
                if self.dynamic_memory:
                    last_action = state_data.get("last_narrative_action")
                    location = state_data.get("location")
                    current_action = state_data.get("current_action")
                    if last_action is not None: self.dynamic_memory.last_narrative_action = last_action; self.logger.info("Loaded last narrative action.")
                    if location is not None: self.dynamic_memory.location = location; self.logger.info("Loaded location: %s", location)
                    if current_action is not None: self.dynamic_memory.current_action = current_action; self.logger.info("Loaded current action (task): %s", current_action)
                    self.dynamic_memory.memories = state_data.get("dynamic_memory", [])
                    self.logger.info("Loaded dynamic memory list (%d items).", len(self.dynamic_memory.memories))
                else: self.logger.error("Cannot load dynamic memory state: dynamic_memory object missing.")

                # Load Explicit State Variables
                self.pending_location_target = state_data.get("pending_location_target", None)
                self.current_topic_focus = state_data.get("current_topic_focus", "Unknown / Resumed")
                self.logger.info("Loaded explicit state - Pending Location: %s, Topic Focus: %s", self.pending_location_target, self.current_topic_focus)

                entered_time_str = state_data.get("location_entered_roleplay_time")
                if entered_time_str:
                    try:
                        entered_time_clean = entered_time_str.split('+')[0].split('Z')[0].split('.')[0]
                        self.location_entered_roleplay_time = datetime.datetime.fromisoformat(entered_time_clean)
                    except ValueError:
                        self.location_entered_roleplay_time = self.current_roleplay_time
                else:
                    self.location_entered_roleplay_time = self.current_roleplay_time
                self.last_time_awareness_note = state_data.get("last_time_awareness_note", "")

                # Load user memory history
                if self.user_memory:
                    user_history = state_data.get("user_memory_history", [])
                    if isinstance(user_history, list): self.user_memory.history = user_history
                    else: self.logger.warning("Loaded user_memory_history is not a list."); self.user_memory.history = []
                    self.logger.info("Loaded user memory history (%d items).", len(self.user_memory.history))
                else: self.logger.error("Cannot load user memory history: user_memory object missing.")

                # --- Cargar Estado del CICLO de Sueño/Vigilia (Controlado por Logic) ---
                self.hours_awake = float(state_data.get("hours_awake", 0.0))
                self.is_sleeping = bool(state_data.get("is_sleeping", False))
                self.hours_slept = float(state_data.get("hours_slept", 0.0))
                self.logger.info("Loaded sleep cycle state - Sleeping: %s, Awake: %.1f hrs, Slept: %.1f hrs",
                                 self.is_sleeping, self.hours_awake, self.hours_slept)
                # --- Fin Carga Ciclo ---

                # Load Emotional Core State (incluyendo fatigue_level desde aquí)
                if self.emotional_core:
                    emo_state = state_data.get("emotional_core_state", {})
                    if emo_state:
                        self.logger.debug("Loading emotional core state attributes: %s", emo_state)
                        # Carga fatiga y tiempo de sueño (si EC aún lo usa internamente)
                        try:
                             # Carga fatiga directamente al atributo de EC
                             self.emotional_core.fatigue_level = float(emo_state.get("fatigue_level", getattr(self.emotional_core, 'fatigue_level', 0.0)))
                             self.logger.info("Loaded fatigue level into EC: %.1f", self.emotional_core.fatigue_level)
                        except (AttributeError, ValueError, KeyError) as fatigue_err: self.logger.warning("Could not load/convert 'fatigue_level' for EC: %s", fatigue_err)

                        # Carga los demás atributos como los tenías
                        try:
                            default_trust = getattr(self.emotional_core, 'current_trust', 0.5)
                            default_intimacy = getattr(self.emotional_core, 'current_intimacy', 0.1)
                            self.emotional_core.current_trust = float(emo_state.get("current_trust", default_trust))
                            self.emotional_core.current_intimacy = float(emo_state.get("current_intimacy", default_intimacy))
                        except (AttributeError, ValueError) as rel_err: self.logger.warning("Could not load/convert 'current_trust' or 'current_intimacy': %s", rel_err)

                        loaded_emotions = emo_state.get("internal_emotions_detailed")
                        if isinstance(loaded_emotions, dict): self.emotional_core.internal_emotions_detailed = loaded_emotions
                        else: self.logger.warning("Loaded internal_emotions_detailed is not a dictionary.")

                        loaded_personality = emo_state.get("personality_traits")
                        if isinstance(loaded_personality, dict): self.emotional_core.personality_traits = loaded_personality
                        else: self.logger.warning("Loaded personality_traits is not a dictionary.")

                        self.emotional_core.attachment_style = emo_state.get("attachment_style", getattr(self.emotional_core, 'attachment_style', 'Unknown'))
                        self.logger.info("Loaded other emotional state attributes (trust, intimacy, emotions, personality, attachment).")
                else: self.logger.error("Cannot load emotional state: emotional_core object missing.")

                self.last_real_time = time.time()
                self.logger.info("General state loaded successfully. Real time tracker reset.")

            except (json.JSONDecodeError, IOError, TypeError, KeyError) as e:
                self.logger.error("Failed to load general state from '%s': %s. Starting with default state.", SAVE_STATE_FILE, e, exc_info=True)
                # Resetear estado a valores por defecto conocidos
                self.current_roleplay_time = datetime.datetime(2025, 4, 16, 14, 0, 0)
                self.pending_location_target = None
                self.current_topic_focus = "Initial Setup / Project Discussion"
                # Resetear estado del ciclo de sueño
                self.hours_awake = 0.0
                self.is_sleeping = False
                self.hours_slept = 0.0
                # Resetear otros componentes si tienen método reset (y si existen)
                # Comentar las llamadas a reset problemáticas
                # if self.dynamic_memory: self.dynamic_memory.reset() # Error: DynamicMemory no tiene método reset
                # if self.user_memory: self.user_memory.reset() # Asumiendo que UM tampoco tiene método reset
                # if self.emotional_core: self.emotional_core.reset() # Asumiendo que EC tampoco tiene método reset
                self.logger.warning("Reset methods for dynamic_memory, user_memory, or emotional_core not implemented or called to avoid errors.")
        else:
            self.logger.info("No general save file '%s' found. Starting with default state.", SAVE_STATE_FILE)


    def _save_state(self):
        """Saves the general state (incluyendo estado del ciclo de sueño) and triggers vector memory save."""
        self.logger.info("Attempting to save comprehensive state to '%s'...", SAVE_STATE_FILE)
        temp_save_file = SAVE_STATE_FILE + ".tmp"
        try:
            # Ensure necessary components exist
            if not all([self.emotional_core, self.dynamic_memory, self.user_memory]):
                 self.logger.error("Cannot save general state: One or more core components are missing.")
                 return

            # Prepare emotional state dictionary safely (incluyendo fatigue_level de EC)
            emo_state_to_save = {
                "internal_emotions_detailed": getattr(self.emotional_core, 'internal_emotions_detailed', {}),
                "personality_traits": getattr(self.emotional_core, 'personality_traits', {}),
                "attachment_style": getattr(self.emotional_core, 'attachment_style', 'Unknown'),
                "current_trust": getattr(self.emotional_core, 'current_trust', None),
                "current_intimacy": getattr(self.emotional_core, 'current_intimacy', None),
                # Guardar fatiga desde EC
                "fatigue_level": getattr(self.emotional_core, 'fatigue_level', None),
            }
            if emo_state_to_save["current_trust"] is None or emo_state_to_save["current_intimacy"] is None:
                 self.logger.warning("Could not save 'current_trust' or 'current_intimacy'.")
            if emo_state_to_save["fatigue_level"] is None:
                 self.logger.warning("Could not save 'fatigue_level' from EmotionalCore.")

            # Prepare main state dictionary (incluyendo estado del ciclo de sueño)
            state_data = {
                "current_roleplay_time": self.current_roleplay_time.isoformat(),
                "last_narrative_action": self.dynamic_memory.last_narrative_action,
                "location": self.dynamic_memory.location,
                "current_action": self.dynamic_memory.current_action,
                "pending_location_target": self.pending_location_target,
                "current_topic_focus": self.current_topic_focus,
                "dynamic_memory": self.dynamic_memory.memories,
                "user_memory_history": self.user_memory.history,
                "emotional_core_state": emo_state_to_save, # Estado emocional con fatiga de EC
                # --- Guardar Estado del CICLO de Sueño/Vigilia (Controlado por Logic) ---
                "hours_awake": self.hours_awake,
                "is_sleeping": self.is_sleeping,
                "hours_slept": self.hours_slept,
                # --- Fin Guardado Ciclo ---
                "location_entered_roleplay_time": self.location_entered_roleplay_time.isoformat() if self.location_entered_roleplay_time else None,
                "last_time_awareness_note": self.last_time_awareness_note,
            }
            self.logger.debug("General state data prepared for saving.")

            # Save general state atomically
            with open(temp_save_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, indent=4, ensure_ascii=False)
            os.replace(temp_save_file, SAVE_STATE_FILE)
            self.logger.info("General state saved successfully to '%s'.", SAVE_STATE_FILE)

            # Trigger saving of vector memory
            if self.vector_memory:
                self.logger.info("Triggering vector memory save...")
                self.vector_memory.save_memory(index_path=VECTOR_INDEX_FILE, data_path=VECTOR_DATA_FILE)
            else:
                 self.logger.warning("Vector memory object not available, skipping vector save.")

        except Exception as e: # Catch potential errors during save
            self.logger.error("Failed during save state process: %s", e, exc_info=True)
            if os.path.exists(temp_save_file):
                try: os.remove(temp_save_file); self.logger.info("Removed temporary general save file '%s' after error.", temp_save_file)
                except OSError as remove_err: self.logger.error("Failed to remove temporary general save file '%s': %s", temp_save_file, remove_err)


    def _update_state_from_input(self, user_input):
        """Detects intent to change location or action from user input."""
        # (Sin cambios respecto a tu versión)
        self.logger.debug("Checking user input for location/action/topic keywords: '%s...'", user_input[:50])
        user_input_lower = user_input.lower()
        locations = { "house": "Poppy's House", "park": "Park", "library": "Library", "school": "School", "science class": "Science Class", "garden": "School Garden", "market": "Mini Market", "store": "Store", "cafe": "Cafe"}
        actions = { "work": "Working on the project", "continue": "Continuing the project", "plan": "Planning the project", "relax": "Relaxing", "start": "Starting the project", "talk": "Talking", "walk": "Walking", "explain": "Explaining situation", "leave": "Leaving current location", "get snacks": "Getting snacks", "eat": "Eating", "study": "Studying"}
        location_intent_detected = False
        action_updated = False
        go_to_keywords = ["go to", "head to", "walk to", "let's go", "at your house", "at my place", "at the", "to the"]
        leave_keywords = ["leave", "exit", "get out of here", "go somewhere else"]
        found_target_loc = None
        if any(phrase in user_input_lower for phrase in go_to_keywords):
            self.logger.debug("Potential 'go to' keyword detected.")
            for keyword, loc_name in locations.items():
                if keyword in user_input_lower:
                    if loc_name != self.dynamic_memory.location and loc_name != self.pending_location_target:
                        self.pending_location_target = loc_name
                        self.logger.info("Pending location target set to: %s based on user input.", loc_name)
                        location_intent_detected = True; break
                    elif loc_name == self.dynamic_memory.location:
                         self.logger.debug("User mentioned current location '%s', no change needed.", loc_name)
                         if self.pending_location_target: self.logger.info("Clearing pending target: %s", self.pending_location_target); self.pending_location_target = None
                         location_intent_detected = True; break
        elif any(phrase in user_input_lower for phrase in leave_keywords):
             self.logger.info("User input suggests leaving current location.")
             if self.pending_location_target: self.logger.info("Clearing pending location target: %s", self.pending_location_target); self.pending_location_target = None
             if self.dynamic_memory.current_action != "Leaving current location": self.dynamic_memory.update_action("Leaving current location", self.active_memory); action_updated = True
             location_intent_detected = True
        found_act = None
        for keyword, act_desc in actions.items():
            if keyword == 'leave' and location_intent_detected: continue
            if keyword in user_input_lower: found_act = act_desc; break
        if found_act and found_act != self.dynamic_memory.current_action:
             old_action = self.dynamic_memory.current_action
             self.dynamic_memory.update_action(found_act, self.active_memory); action_updated = True
             self.logger.info("Action updated from '%s' to '%s' based on user input.", old_action, found_act)
        if not location_intent_detected and not action_updated: self.logger.debug("No location intent or action change keywords found in user input.")


    def _update_topic_focus(self, user_input, ai_response):
        """(Basic) Updates the current topic focus based on keywords."""
        # (Sin cambios respecto a tu versión)
        text_to_scan = (user_input + " " + ai_response).lower()
        new_topic = self.current_topic_focus
        project_keywords = ["project", "work", "task", "notes", "deadline", "teacher", "science class", "research", "presentation", "study", "worksheet", "diagram"]
        emotional_keywords = ["feel", "feeling", "sad", "happy", "angry", "scared", "sorry", "overdose", "medication", "pills", "anxiety", "depress", "breakdown", "scars", "kill myself", "hug", "talk", "explain", "happened", "yesterday", "worried", "concern", "space", "think"]
        location_keywords = ["house", "place", "garden", "school", "library", "market", "store", "cafe", "where are we", "go to", "leave", "outside", "inside"]
        relationship_keywords = ["friend", "partner", "trust", "relationship", "together", "us"]
        food_keywords = ["eat", "hungry", "snacks", "food", "drink", "cafe", "market"]
        topic_detected = False
        if any(kw in text_to_scan for kw in emotional_keywords): new_topic = "Personal/Emotional Discussion"; topic_detected = True
        elif any(kw in text_to_scan for kw in location_keywords) or self.pending_location_target: new_topic = "Location/Transition Discussion"; topic_detected = True
        elif any(kw in text_to_scan for kw in food_keywords): new_topic = "Food/Snacks Discussion"; topic_detected = True
        elif any(kw in text_to_scan for kw in project_keywords): new_topic = "Project Discussion"; topic_detected = True
        elif any(kw in text_to_scan for kw in relationship_keywords): new_topic = "Relationship Dynamics"; topic_detected = True
        if not topic_detected:
             if "project" in self.dynamic_memory.current_action.lower(): new_topic = "Project Discussion"
             elif "talk" in self.dynamic_memory.current_action.lower() or "explain" in self.dynamic_memory.current_action.lower(): new_topic = "General Discussion / Explanation"
        if new_topic != self.current_topic_focus:
            self.logger.info("Topic focus updated from '%s' to '%s'", self.current_topic_focus, new_topic)
            self.current_topic_focus = new_topic
        else: self.logger.debug("Topic focus remains: '%s'", self.current_topic_focus)



    def _build_time_awareness_note(self):
        """Build a natural language time note for prompt conditioning."""
        current_hour = self.current_roleplay_time.hour
        if 0 <= current_hour < 5:
            day_phase = "late night"
        elif 5 <= current_hour < 12:
            day_phase = "morning"
        elif 12 <= current_hour < 18:
            day_phase = "afternoon"
        elif 18 <= current_hour < 22:
            day_phase = "evening"
        else:
            day_phase = "night"

        minutes_in_location = 0
        if self.location_entered_roleplay_time:
            minutes_in_location = max(0, int((self.current_roleplay_time - self.location_entered_roleplay_time).total_seconds() // 60))

        notes = [f"It is currently {day_phase}."]
        if minutes_in_location >= 30:
            notes.append(f"You have been at this location for about {minutes_in_location} minutes.")
        if self.is_sleeping:
            notes.append("You are currently sleeping and not fully responsive.")
        elif current_hour >= 23 or current_hour < 6:
            notes.append("The hour is late; you may feel slower, more tired, or eager to wrap things up.")

        note = " ".join(notes)
        self.last_time_awareness_note = note
        return note, day_phase, minutes_in_location

    def construct_context(self, user_input):
        """Constructs the context dictionary, including RAG memories and fatigue/sleep state from EC."""
        self.logger.debug("--- Logic: construct_context called ---")
        if not self.dynamic_memory:
             self.logger.error("DynamicMemory not initialized in construct_context. Returning empty context.")
             return {}
        if not self.emotional_core:
             self.logger.error("EmotionalCore not initialized in construct_context. Returning empty context.")
             return {} # EC es necesario para fatiga

        # --- Get Base State ---
        dyn_state = self.dynamic_memory.current_state()
        user_state = self.user_memory.get_user_info() if self.user_memory else {}
        previous_narrative_action = self.dynamic_memory.last_narrative_action
        current_time_str = self.current_roleplay_time.strftime("%A, %I:%M %p")
        current_location = dyn_state.get('location', 'Unknown')
        self.logger.debug("Dynamic state fetched: %s", dyn_state)

        time_awareness_note, day_phase, minutes_in_location = self._build_time_awareness_note()

        # --- RAG Retrieval ---
        retrieved_memories_text = []
        if self.vector_memory:
            try:
                query = f"{user_input} Topic: {self.current_topic_focus}"
                self.logger.info(f"Retrieving relevant memories for query: '{query[:100]}...'")
                retrieved_memories_full = self.vector_memory.retrieve_relevant_memories(query, k=5)
                retrieved_memories_text = [mem.get('text', '') for mem in retrieved_memories_full if mem.get('text')]
                self.logger.info(f"Retrieved {len(retrieved_memories_text)} relevant memories via RAG.")
                self.logger.debug("Retrieved RAG memories: %s", retrieved_memories_text)
            except Exception as e:
                self.logger.error(f"Error during RAG retrieval: {e}", exc_info=True)
                retrieved_memories_text = ["Error retrieving relevant memories."]
        else:
            self.logger.warning("VectorMemoryStore not available, skipping RAG retrieval.")

        # --- Context Flags & Emotional Core ---
        context_flags = {
            "location_type": "public" if current_location not in ["Poppy's House"] else "private",
            "recent_failure": any("fail" in mem.lower() for mem in dyn_state.get('recent_memories', '').split(" | ") if mem),
            "high_impact_event": any(word in user_input.lower() for word in ["die", "death", "gone", "kill", "razor", "cut", "suicide", "depress", "overdose", "scars"])
        }

        # Bring in persisted long-term summaries (legacy path via ActiveMemory -> LongTermMemoryFile)
        long_term_summaries = []
        if self.long_term_memory_legacy:
            try:
                long_term_summaries = self.long_term_memory_legacy.get_memories()[-5:]
            except Exception as ltm_err:
                self.logger.warning("Could not fetch long-term summaries: %s", ltm_err)

        # Lightweight internal objective to improve coherence and initiative
        if context_flags["high_impact_event"]:
            internal_objective = "Stabilize the moment emotionally while staying in character."
        elif self.pending_location_target:
            internal_objective = f"Complete transition toward {self.pending_location_target} and keep user engaged."
        elif "Project" in self.current_topic_focus:
            internal_objective = "Progress the project discussion with concrete next steps."
        elif "Relationship" in self.current_topic_focus or "Emotional" in self.current_topic_focus:
            internal_objective = "Deepen trust gradually without breaking character tone."
        else:
            internal_objective = "Maintain narrative continuity and move the scene forward."
        context_flags["current_topic"] = self.current_topic_focus
        context_flags["is_transitioning_location"] = bool(self.pending_location_target)
        # Pasar estado de sueño/fatiga (desde Logic/EC) a EC si este lo usa en sus cálculos
        context_flags["current_fatigue"] = self.emotional_core.fatigue_level
        context_flags["is_sleeping"] = self.is_sleeping
        self.logger.debug("Context flags determined: %s", context_flags)

        # Llamar a EC para obtener guía emocional
        self.logger.debug("Processing interaction with EmotionalCore...")
        emotional_guidance = self.emotional_core.process_interaction(user_input, context_flags)
        self.last_emotional_guidance = emotional_guidance
        self.logger.debug("Emotional guidance received (keys): %s", emotional_guidance.keys())

        char_base = self.character_memory.get_character_info() if self.character_memory else {}
        self.logger.debug("Character base info fetched.")

        # --- Assemble Final Context Dictionary ---
        self.logger.debug("Assembling final context dictionary...")
        # Obtener nivel de fatiga actual desde EC
        current_fatigue_level = self.emotional_core.fatigue_level

        context_dict = {
            "character_name": char_base.get('name', 'Poppy'),
            "personality": char_base.get('personality', 'Unknown'),
            "location": current_location,
            "pending_location": self.pending_location_target,
            "action": dyn_state.get('action', 'Unknown'),
            "topic_focus": self.current_topic_focus,
            "current_time_in_roleplay": current_time_str,
            "day_phase": day_phase,
            "minutes_in_location": minutes_in_location,
            "time_awareness_note": time_awareness_note,
            "high_impact_event": context_flags["high_impact_event"],
            "emotional_guidance": emotional_guidance,
            "previous_action": previous_narrative_action,
            "dynamic_memory": dyn_state.get('recent_memories', '').split(" | ") if dyn_state.get('recent_memories') else [],
            "retrieved_memories": retrieved_memories_text, # RAG results
            "long_term_summaries": long_term_summaries,
            "internal_objective": internal_objective,
            "user_name": user_state.get('name', 'User'),
            "user_input": user_input,
            "user_memories": self.user_memory.history[-3:] if self.user_memory and self.user_memory.history else [],
            # --- Añadir Estado de Sueño/Fatiga y Constantes Necesarias al Contexto ---
            "is_sleeping": self.is_sleeping, # Desde Logic
            "fatigue_level": current_fatigue_level, # Desde EmotionalCore
            "fatigue_threshold_wake": FATIGUE_THRESHOLD_WAKE, # Constante de Logic
            "fatigue_threshold_sleep": FATIGUE_THRESHOLD_SLEEP, # Constante de Logic
            # --- Fin ---
        }

        self.logger.info("Context constructed successfully.")
        self.logger.debug("--- Logic: construct_context finished ---")
        return context_dict


    def manage_dynamic_memory(self, user_input, full_ai_response):
        """Manages state updates AFTER a turn (time, fatigue/sleep, memory, state resolution)."""
        self.logger.debug("--- Logic: manage_dynamic_memory called ---")
        if not all([self.dynamic_memory, self.user_memory, self.character_memory, self.emotional_core]):
             self.logger.error("Cannot manage memory/state: Core components missing.")
             return

        self.logger.debug("User input: '%s...'", user_input[:100])
        self.logger.debug("Full AI response: '%s...'", full_ai_response[:150])

        # --- 1. Update Explicit State based on Input ---
        self._update_state_from_input(user_input)

        # --- 2. Update Topic Focus based on Turn ---
        self._update_topic_focus(user_input, full_ai_response)

        # --- 3. Time Advancement & Fatiga/Sueño Logic ---
        current_real_time = time.time()
        real_delta_seconds = current_real_time - self.last_real_time
        self.logger.debug("Real time delta since last turn: %.2f seconds", real_delta_seconds)
        self.last_real_time = current_real_time
        roleplay_delta_scaled = datetime.timedelta(seconds=real_delta_seconds * self.time_scale_factor)
        roleplay_delta = max(roleplay_delta_scaled, self.min_time_advance_per_turn)

        if roleplay_delta:
            self.current_roleplay_time += roleplay_delta
            self.logger.info("Roleplay time advanced by %s to: %s", roleplay_delta, self.current_roleplay_time.strftime("%Y-%m-%d %H:%M:%S"))

            time_delta_hours = roleplay_delta.total_seconds() / 3600.0

            # --- Actualizar Fatiga llamando a Emotional Core ---
            if self.emotional_core:
                self.logger.debug(f"Calling EC.update_fatigue_state({time_delta_hours:.2f}, {self.is_sleeping})")
                self.emotional_core.update_fatigue_state(time_delta_hours, self.is_sleeping)
                current_fatigue = self.emotional_core.fatigue_level
                self.logger.info(f"Fatigue level updated by EC to: {current_fatigue:.1f}")
            else:
                self.logger.error("EmotionalCore not available, cannot update fatigue.")
                current_fatigue = 50.0 # Fallback?

            # --- Lógica del CICLO de Sueño/Vigilia (Controlado por Logic) ---
            was_sleeping_before = self.is_sleeping # Guardar estado anterior para detectar cambio

            if self.is_sleeping:
                self.hours_slept += time_delta_hours
                self.logger.debug(f"Sleeping... Hours slept: {self.hours_slept:.1f}")

                # Lógica para despertar (usa fatiga de EC)
                time_to_wake_up = (
                    current_fatigue <= FATIGUE_THRESHOLD_WAKE and
                    self.hours_slept >= MIN_SLEEP_HOURS
                )
                force_wake_up = self.hours_slept > 10 or self.current_roleplay_time.hour > 9

                if time_to_wake_up or force_wake_up:
                    self.is_sleeping = False
                    self.hours_awake = 0.0 # Resetea horas despierto al despertar
                    self.hours_slept = 0.0 # Resetea horas dormido
                    self.logger.info(f"Woke up at {self.current_roleplay_time.strftime('%H:%M')}. Fatigue (from EC): {current_fatigue:.1f}")
                    # Podríamos añadir un evento a memoria vectorial aquí

            else: # Está despierto
                self.hours_awake += time_delta_hours
                self.logger.debug(f"Awake... Hours awake: {self.hours_awake:.1f}")

                # Lógica para intentar dormir (usa fatiga de EC)
                current_hour = self.current_roleplay_time.hour
                is_sleep_time = False
                if SLEEP_START_HOUR <= SLEEP_END_HOUR: is_sleep_time = SLEEP_START_HOUR <= current_hour < SLEEP_END_HOUR
                else: is_sleep_time = current_hour >= SLEEP_START_HOUR or current_hour < SLEEP_END_HOUR

                needs_sleep_fatigue = current_fatigue >= FATIGUE_THRESHOLD_SLEEP
                needs_sleep_hours = self.hours_awake >= MAX_AWAKE_HOURS

                if (needs_sleep_fatigue or needs_sleep_hours) and is_sleep_time:
                    self.is_sleeping = True
                    self.hours_slept = 0.0 # Resetea horas dormido al empezar a dormir
                    self.logger.info(f"Fell asleep at {self.current_roleplay_time.strftime('%H:%M')}. Fatigue (from EC): {current_fatigue:.1f}")
                    # Podríamos añadir un evento a memoria vectorial aquí
            # --- Fin Lógica Ciclo ---

            # --- Llamar a _process_sleep_cycle en EC si acaba de dormirse ---
            if self.emotional_core and not was_sleeping_before and self.is_sleeping:
                 self.logger.info("Sleep started. Calling EmotionalCore._process_sleep_cycle().")
                 try:
                     self.emotional_core._process_sleep_cycle()
                 except Exception as e_proc:
                     self.logger.error(f"Error calling _process_sleep_cycle: {e_proc}", exc_info=True)
            # --- Fin llamada a _process_sleep_cycle ---

        else:
            self.logger.warning("No valid time delta calculated. Skipping time and fatigue update.")
        # --- Fin Time Advancement & Fatiga/Sueño ---

        # --- 4. Resolve Pending Location Change (Tuned v2) --- # <-- MODIFIED SECTION START ---
        if self.pending_location_target:
            self.logger.debug(f"Pending location target exists: {self.pending_location_target}. Checking AI action for movement cues...")

            # Extract action part from AI response
            action_match = self.action_regex.search(full_ai_response)
            ai_action_text = action_match.group(1).lower() if action_match else ""

            # Palabras clave en minúsculas para indicar movimiento o llegada DENTRO DE LA ACCIÓN
            movement_keywords_in_action = [
                "walks", "walked", "walking", "heads", "headed", "heading", "goes", "went", "going",
                "arrives", "arrived", "arriving", "enters", "entered", "entering", "reaches", "reached", "reaching",
                "follows", "following", "leads", "leading", "moves", "moved", "moving",
                "steps out", "steps in", "goes outside", "goes inside"
                # Removed dialogue-like phrases like "let's go" from action check
                # Removed location names from action check (e.g., "at the house")
            ]

            # Check if the ACTION part of the AI response indicates movement towards the destination
            ai_action_indicates_movement = any(keyword in ai_action_text for keyword in movement_keywords_in_action)

            if ai_action_indicates_movement:
                current_loc_before_move = self.dynamic_memory.location
                if current_loc_before_move != self.pending_location_target:
                    self.logger.info(f"AI ACTION indicates movement. Resolving pending location change: Moving from '{current_loc_before_move}' to '{self.pending_location_target}'")
                    self.dynamic_memory.update_location(self.pending_location_target, self.active_memory)
                    self.location_entered_roleplay_time = self.current_roleplay_time
                    # Resetear acción/tema si el cambio es significativo (e.g., leaving school)
                    if current_loc_before_move in ["School", "Library", "Science Class"] and self.dynamic_memory.location not in ["School", "Library", "Science Class"]:
                         self.dynamic_memory.update_action("Settling in new location", self.active_memory)
                         self.current_topic_focus = "Location Change / Settling In"
                         self.logger.info("Action and Topic reset due to significant location change.")
                    self.pending_location_target = None # Limpiar objetivo después del movimiento exitoso
                else:
                     self.logger.debug("Pending location target matches current location. Clearing target as AI action acknowledged movement.")
                     self.pending_location_target = None # Limpiar objetivo aunque ya esté allí
            else:
                self.logger.info(f"AI action ('{ai_action_text[:50]}...') did not contain clear movement cues. Deferring location change to {self.pending_location_target}.")
                # Mantener self.pending_location_target para el siguiente turno
        # --- End Location Resolution (Tuned v2) --- # <-- MODIFIED SECTION END ---


        # --- 5. Add Events to Memories ---
        user_state = self.user_memory.get_user_info()
        char_name = self.character_memory.get_character_info().get('name', 'Character')
        # Obtener estado emocional y fatiga actual de EC para el log
        current_emotional_state_labels = self.last_emotional_guidance.get('emotional_state', [])
        current_emotions_detailed = self.last_emotional_guidance.get('internal_emotions_detailed', {})
        current_fatigue_for_log = self.emotional_core.fatigue_level if self.emotional_core else "N/A"
        self.logger.debug("Current emotional state labels for event log: %s", current_emotional_state_labels)

        # Event string for RAG/embedding
        event_for_rag = (f"User: '{user_input}'\n"
                         f"{char_name}: '{full_ai_response}'")
        self.logger.debug("Constructed event string for RAG: '%s...'", event_for_rag[:250])

        # Event string for dynamic memory log
        event_log_string = (f"User: '{user_input}'. {char_name}: '{full_ai_response}'. "
                            f"[Loc: {self.dynamic_memory.location}] [Act: {self.dynamic_memory.current_action}] "
                            f"[Topic: {self.current_topic_focus}] [Pending: {self.pending_location_target if self.pending_location_target else 'None'}] "
                            f"[Emo: {', '.join(current_emotional_state_labels)}] [Fatigue: {current_fatigue_for_log:.1f}] [Sleeping: {self.is_sleeping}]") # Usar fatiga de EC
        self.logger.debug("Constructed event string for dynamic log: '%s...'", event_log_string[:300])

        # Add detailed log string to dynamic memory
        self.logger.debug("Calling dynamic_memory.add_memory...")
        if self.active_memory:
             self.dynamic_memory.add_memory(event_log_string, self.active_memory)
        else:
             self.logger.warning("Active memory object missing, cannot pass to dynamic_memory.add_memory.")
             self.dynamic_memory.add_memory(event_log_string)

        # Add concise event string + metadata to Vector Memory Store (RAG)
        if self.vector_memory:
            self.logger.debug("Calling vector_memory.add_memory...")
            metadata = {
                "timestamp": time.time(),
                "roleplay_time": self.current_roleplay_time.isoformat(),
                "location": self.dynamic_memory.location,
                "action": self.dynamic_memory.current_action,
                "topic": self.current_topic_focus,
                "emotions": current_emotions_detailed,
                "fatigue": current_fatigue_for_log, # Usar fatiga de EC
                "is_sleeping": self.is_sleeping # Usar estado de Logic
            }
            self.vector_memory.add_memory(event_for_rag, metadata=metadata)
        else: self.logger.warning("Vector memory not available, skipping add.")

        # Add AI's response to user's memory history
        user_memory_entry = f"{char_name} said: '{full_ai_response}'"
        self.logger.debug("Adding to user_memory: '%s...'", user_memory_entry[:100])
        self.user_memory.add_memory(user_memory_entry)

        # --- 6. Extract and Store Last Narrative Action ---
        self.logger.debug("Attempting to extract narrative action from response...")
        extracted_action = "*[Action could not be parsed]*"
        match = self.action_regex.search(full_ai_response)
        if match: extracted_action = f"*{match.group(1).strip()}*"; self.logger.debug("Action extracted using regex: %s", extracted_action)
        else:
             lines = full_ai_response.split('\n', 1); first_line = lines[0].strip()
             if len(first_line) < 150 and first_line.startswith("*") and first_line.endswith("*") and len(first_line.split()) > 1: extracted_action = first_line; self.logger.warning("Using first line fallback for action: %s", extracted_action)
             else: self.logger.warning("Could not parse narrative action from response: '%s...'", full_ai_response[:100])
        memory_logger.debug("Setting last narrative action in DynamicMemory: %s", extracted_action)
        self.dynamic_memory.set_last_narrative_action(extracted_action)

        # --- Finish ---
        self.logger.info("Memory and State managed for turn.")
        self.logger.debug("--- Logic: manage_dynamic_memory finished ---")

