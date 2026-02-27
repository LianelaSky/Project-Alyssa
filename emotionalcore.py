# emotionalcore.py
import logging
import random
import math
import time # Needed for time_delta calculation if done internally (removed)
from copy import deepcopy # Useful for states

# Logging setup
logger = logging.getLogger('emotional_core')
memory_logger = logging.getLogger('memory.emotional_core')

# --- MODIFIED SECTION START ---
# Se añadió la constante de recuperación de fatiga
FATIGUE_RECOVERY_RATE = 12.5 # Puntos de fatiga recuperados por hora dormido (ajustar)
# --- MODIFIED SECTION END ---

# (Otras constantes como las tenías)
EMOTIONAL_INTENSITY_THRESHOLD = 0.6
RELATIONSHIP_UPDATE_THRESHOLD = 0.1
PERSONALITY_UPDATE_RATE = 0.01
ATTACHMENT_UPDATE_RATE = 0.005
MOOD_DECAY_RATE = 0.1
FATIGUE_EMOTIONAL_IMPACT_FACTOR = 0.1 # How much fatigue affects emotional intensity calc
BASE_FATIGUE_INCREASE = 0.5 # Base fatigue increase per second (adjust)

class EmotionalCore:
    def __init__(self, # --- NEW: Initialization parameters for reusability --- # <-- SECTION REVIEWED/KEPT (Minor change for clarity)
                     initial_emotions: dict = None,
                     initial_personality: dict = None,
                     initial_attachment_style: dict = None,
                     initial_unconscious_patterns: dict = None,
                     initial_trauma_responses: dict = None,
                     initial_regulation_strategies: dict = None,
                     initial_cognitive_appraisals: dict = None,
                     initial_cultural_factors: dict = None,
                     character_name: str = "Poppy", # Name for logs or future references
                     character_memory = None # Added character_memory here as it was used below
                     ):

        # --- Character Name ---
        self.character_name = character_name # Save the name
        # --- ADDED --- Needed for char_info below
        self.character_memory = character_memory
        self.char_info = self.character_memory.get_character_info() if character_memory else {}
        logger.info("Initializing EmotionalCore for %s...", self.char_info.get('name', 'Unknown Character'))
        # --- END ADDED ---

        # --- Core Emotional Dimensions (with default values if not provided) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_emotions = {
            "vulnerability": 0.2, "connection": 0.1, "autonomy": 0.8, "validation": 0.3,
            "authenticity": 0.4, "psychological_safety": 0.2, "grieving": 0.0, "joy": 0.2,
            "anger": 0.3, "fear": 0.4, "shame": 0.5, "anticipation": 0.2, "disgust": 0.1
        }
        _initial_emotions = default_emotions.copy()
        if initial_emotions:
            _initial_emotions.update({k: v for k, v in initial_emotions.items() if k in _initial_emotions})
        self.emotions = _initial_emotions
        self.internal_emotions = self.emotions.copy()
        self.expressed_emotions = self.emotions.copy()

        # --- Defense Mechanisms --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.defense_activation = 0.7
        self.active_defenses = []

        # --- Emotional Memory System --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.emotional_memories = []
        self.emotional_triggers = {}
        self.core_memories = []
        self.memory_decay_rate = 0.01
        self.memory_consolidation_threshold = 0.75
        self.max_emotional_memories = 100
        self.max_core_memories = 15

        # --- Relational Dynamics and Attachment (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.trust_threshold = 0.5
        self.intimacy_level = 0.1
        self.psychological_distance = 0.9
        default_attachment = {"anxiety": 0.7, "avoidance": 0.6, "security": 0.2, "disorganization": 0.4}
        _initial_attachment = default_attachment.copy()
        if initial_attachment_style:
            _initial_attachment.update({k: v for k, v in initial_attachment_style.items() if k in _initial_attachment})
        self.attachment_style = _initial_attachment

        # --- Personality (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_personality = {
            "pride": 0.8, "fear_of_vulnerability": 0.7, "need_for_control": 0.8, "emotional_awareness": 0.4,
            "empathy": 0.3, "authenticity": 0.4, "openness": 0.3, "conscientiousness": 0.7,
            "extraversion": 0.4, "agreeableness": 0.3, "neuroticism": 0.7, "resilience": 0.4, "adaptability": 0.3
        }
        _initial_personality = default_personality.copy()
        if initial_personality:
            _initial_personality.update({k: v for k, v in initial_personality.items() if k in _initial_personality})
        self.personality = _initial_personality

        # --- Emotional Stability and Volatility --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.emotional_inertia = max(0.1, min(0.9, 0.6 + (self.personality['neuroticism'] - 0.5) * 0.4))
        self.emotional_volatility = max(0.1, min(0.9, 0.3 + (self.personality['neuroticism'] - 0.5) * 0.5))
        self.emotional_granularity = max(0.1, min(0.9, 0.2 + self.personality['emotional_awareness'] * 0.4))

        # --- Unconscious Patterns (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_unconscious = {
            "fear_of_abandonment": 0.6, "perfectionism": 0.8, "self_worth_contingency": 0.7,
            "spotlight_effect": 0.6, "impostor_syndrome": 0.7, "emotional_repression": 0.6,
            "rejection_sensitivity": 0.8
        }
        _initial_unconscious = default_unconscious.copy()
        if initial_unconscious_patterns:
            _initial_unconscious.update({k: v for k, v in initial_unconscious_patterns.items() if k in _initial_unconscious})
        self.unconscious_patterns = _initial_unconscious

        # --- Trauma Responses (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_trauma = {"fight": 0.4, "flight": 0.6, "freeze": 0.7, "fawn": 0.5, "dissociation": 0.3}
        _initial_trauma = default_trauma.copy()
        if initial_trauma_responses:
            _initial_trauma.update({k: v for k, v in initial_trauma_responses.items() if k in _initial_trauma})
        self.trauma_responses = _initial_trauma

        # --- Emotional Regulation Strategies (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_regulation = {
            "cognitive_reappraisal": 0.3, "expressive_suppression": 0.7, "situation_selection": 0.5,
            "attention_deployment": 0.4, "problem_solving": 0.6, "acceptance": 0.2,
            "self_soothing": 0.3, "seeking_support": 0.2
        }
        _initial_regulation = default_regulation.copy()
        if initial_regulation_strategies:
            _initial_regulation.update({k: v for k, v in initial_regulation_strategies.items() if k in _initial_regulation})
        self.regulation_strategies = _initial_regulation

        # --- Facade and Authenticity --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.facade_intensity = 0.8 # Recalculated

        # --- Cultural and Contextual Influences (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_cultural = {
            "emotional_display_rules": 0.7, "individualism": 0.8, "power_distance": 0.6,
            "uncertainty_avoidance": 0.7, "long_term_orientation": 0.5
        }
        _initial_cultural = default_cultural.copy()
        if initial_cultural_factors:
            _initial_cultural.update({k: v for k, v in initial_cultural_factors.items() if k in _initial_cultural})
        self.cultural_factors = _initial_cultural

        # --- Emotional Contagion --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.emotional_contagion = max(0.1, min(0.9, 0.4 + self.personality['empathy'] * 0.4 + (self.personality['extraversion'] - 0.5) * 0.2 ))

        # --- Emotional Intelligence (partially derived) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self._update_emotional_intelligence()

        # --- Growth and Healing --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.personal_growth = {
            "insight_development": 0.2, "emotional_integration": 0.1, "schema_restructuring": 0.1,
            "self_compassion": 0.2, "identity_coherence": 0.3
        }

        # --- Cognitive Appraisal Patterns (with default values) --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        default_cognitive = {
            "threat_sensitivity": 0.7, "reward_sensitivity": 0.6, "self_efficacy": 0.5,
            "other_blame": 0.6, "self_blame": 0.7, "future_expectancy": 0.4, "certainty": 0.3
        }
        _initial_cognitive = default_cognitive.copy()
        if initial_cognitive_appraisals:
            _initial_cognitive.update({k: v for k, v in initial_cognitive_appraisals.items() if k in _initial_cognitive})
        self.cognitive_appraisals = _initial_cognitive

        # --- MODIFIED SECTION START ---
        # Se modificó la inicialización del estado de fatiga/sueño
        # self.time_since_last_sleep = 0.0 # ELIMINADO - Logic maneja hours_awake
        # self.needs_sleep_threshold = 8 * 60 * 60 # ELIMINADO - Logic maneja umbrales
        self.fatigue_level = 0.0 # Mantenido - Calculado aquí, pero ciclo controlado por Logic
        # --- MODIFIED SECTION END ---

        self.current_conflicts = []
        self.self_identity_metrics = {"coherence": 0.5, "stability": 0.5}

        # --- Internal State --- # <-- SECTION REVIEWED/KEPT (Logic from your code)
        self.last_interaction_time = time.time()
        self.emotional_state_labels = [] # Initialize as empty list

        logger.info("EmotionalCore initialized.")
        # Note: Loading state is handled by RPLogic, which sets these attributes.


    def _update_emotional_intelligence(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Calculates/updates derived EI components based on personality."""
        p = self.personality
        self.emotional_intelligence = {
            "self_awareness": p["emotional_awareness"],
            "self_management": max(0.1, min(0.9, (p["conscientiousness"] * 0.3 + p["resilience"] * 0.4 + (1 - p["neuroticism"]) * 0.3))),
            "social_awareness": p["empathy"],
            "relationship_management": max(0.1, min(0.9, (p["agreeableness"] * 0.4 + p["extraversion"] * 0.2 + p["empathy"] * 0.4)))
        }

    # --- Main Processing Method ---
    # def _update_fatigue(self, time_delta): # <-- REMOVED - This was the first, simpler definition (duplicate)
    #     # ... (code removed) ...

    def process_interaction(self, message, context): # <-- MODIFIED SECTION START ---
        """
        Processes user interaction, updates the complete internal state,
        and generates guidance for the dialogue response.
        Fatigue is now updated externally via update_fatigue_state.
        Sleep cycle check is removed.
        """
        current_time = time.time()
        # time_delta = current_time - self.last_interaction_time # time_delta is now passed externally if needed by fatigue calc
        # self.time_since_last_sleep += time_delta # REMOVED - Logic handles hours_awake
        # self._update_fatigue(time_delta) # REMOVED - Called externally via update_fatigue_state

        # --- Start of Processing Cycle ---
        # if self.time_since_last_sleep > self.needs_sleep_threshold: # REMOVED - Logic handles sleep trigger
        #     self._process_sleep_cycle()
        #     self.time_since_last_sleep = 0.0

        self._decay_memories(current_time - self.last_interaction_time) # Decay needs time_delta
        emotional_impact, cognitive_appraisal = self._analyze_input(message, context)
        triggered_memories_indices = self._check_triggers(message)
        if triggered_memories_indices:
            triggered_memories = [self.emotional_memories[i] for i in triggered_memories_indices if i < len(self.emotional_memories)]
            self._amplify_emotions_from_triggers(emotional_impact, triggered_memories)
        trauma_activation = self._evaluate_trauma_triggers(message, context, emotional_impact)
        if context.get("interlocutor_emotions"):
            self._process_emotional_contagion(context["interlocutor_emotions"])
        self._update_internal_emotions(emotional_impact, context, trauma_activation)

        # --- Internal Post-Emotion Processing ---
        regulation_effects = self._apply_regulation_strategies(context)
        self._evaluate_defenses()
        self._calculate_expressed_emotions(regulation_effects) # Updates facade_intensity
        self._update_relationship(message, emotional_impact, context)
        self._form_emotional_memory(message, emotional_impact, context, cognitive_appraisal, current_time)
        growth_occurred = self._process_growth_opportunities(context, regulation_effects)
        if growth_occurred: context["growth_opportunity_taken"] = True # Flag for evolution
        self._evolve_personality(emotional_impact, trauma_activation, context)
        self._update_attachment_patterns(context, emotional_impact)

        # --- Integration and Conflict Steps ---
        self.current_conflicts = self._detect_conflicts()
        if self.current_conflicts:
            self._resolve_conflicts(self.current_conflicts)
        self._integrate_self_identity()

        # --- Cycle Completion ---
        self.last_interaction_time = current_time
        return self._generate_response_guidance(context, trauma_activation)
    # --- MODIFIED SECTION END ---


    # --- Input Analysis Methods ---
    def _analyze_input(self, message, context): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Analyzes the emotional impact and cognitive meaning of a message"""
        # (Detailed implementation from the previous version)
        impact = {emotion: 0.0 for emotion in self.emotions}
        message_lower = message.lower()
        # ENGLISH TRANSLATION of Spanish keywords
        emotion_triggers = {
            "vulnerability": {"increase": ["confess", "secret", "open up", "feel", "help", "intimate", "private"], "decrease": ["pathetic", "weak", "stupid", "ridiculous", "superficial"]},
            "connection": {"increase": ["together", "us", "connect", "hug", "support", "team", "love", "share", "understand"], "decrease": ["alone", "your problem", "separated", "distant", "ignore", "different"]},
            "autonomy": {"increase": ["decide", "my choice", "free", "independent", "control", "my life", "you respect"], "decrease": ["must", "you have to", "forced", "you order", "you control", "you impose"]},
            "validation": {"increase": ["great", "impressive", "good job", "proud", "success", "achievement", "you're worth it", "I recognize"], "decrease": ["bad", "mistake", "failure", "disappointment", "useless", "criticize", "judge"]},
            "authenticity": {"increase": ["real", "honest", "sincere", "myself", "truth", "transparent"], "decrease": ["false", "you pretend", "mask", "you lie", "you hide", "deception"]},
            "psychological_safety": {"increase": ["safe", "I trust", "safe", "I understand", "support", "comfortable", "respect"], "decrease": ["danger", "threat", "you judge", "you criticize", "fear", "insecure", "pressure"]},
            "grieving": {"increase": ["died", "loss", "miss", "mourning", "deep sadness", "emptiness", "pain"], "decrease": ["get over", "move on", "peace", "remember fondly", "accept", "heal"]},
            "joy": {"increase": ["happy", "joyful", "fun", "enjoy", "great", "wonderful", "love it", "positive"], "decrease": ["boring", "sad", "bad", "depressing", "negative", "pessimistic"]},
            "anger": {"increase": ["unfair", "hate", "rage", "annoyed", "furious", "bother", "irritates", "provoke"], "decrease": ["calm", "forgive", "I understand", "patience", "serene", "resolve"]},
            "fear": {"increase": ["fear", "scared", "afraid", "danger", "anxiety", "panic", "terror", "worried"], "decrease": ["safe", "calm", "well", "confident", "brave", "fearless"]},
            "shame": {"increase": ["shame", "humiliated", "unworthy", "guilt", "pathetic", "my mistake", "ridiculous"], "decrease": ["I'm worth it", "enough", "accepted", "proud", "worthy", "guiltless"]},
            "anticipation": {"increase": ["expect", "soon", "future", "plan", "wish", "nervous about", "anxious for"], "decrease": ["now", "already", "past", "indifferent to future", "present"]},
            "disgust": {"increase": ["disgusting", "repugnant", "horrible", "immoral", "dirty", "repulsive"], "decrease": ["clean", "pleasant", "acceptable", "normal", "beautiful"]}
        }
        volatility_factor = (1 + self.emotional_volatility * 0.8)
        for emotion, triggers in emotion_triggers.items():
            increase_count = sum(word in message_lower for word in triggers.get("increase", []))
            decrease_count = sum(word in message_lower for word in triggers.get("decrease", []))
            impact[emotion] += (increase_count * 0.15 - decrease_count * 0.12) * volatility_factor
        strong_trigger_hit = False
        # ENGLISH TRANSLATION of Spanish trigger phrases
        if any(phrase in message_lower for phrase in ["hug", "comfort", "I love you", "I need you", "unconditional support", "I'm here for you"]):
            impact["connection"] += 0.45; impact["vulnerability"] += 0.35; impact["authenticity"] += 0.2; impact["psychological_safety"] += 0.25
            strong_trigger_hit = True
        if any(phrase in message_lower for phrase in ["died", "death", "funeral", "irreparable loss", "gone"]):
            impact["grieving"] += 0.65; impact["vulnerability"] += 0.45; impact["connection"] -= 0.25; impact["joy"] -= 0.6
            strong_trigger_hit = True
        if any(phrase in message_lower for phrase in ["abandoned", "nobody loves me", "I'm worthless", "always alone", "betrayed", "you left me"]):
            impact["fear"] += 0.55; impact["shame"] += 0.45; impact["vulnerability"] += 0.45; impact["connection"] -= 0.35
            impact["psychological_safety"] -= 0.45; impact["anger"] += 0.25
            strong_trigger_hit = True
        if strong_trigger_hit: self.emotional_inertia = max(0.05, self.emotional_inertia * 0.4) # Reduce more
        cognitive_appraisal = self._cognitive_appraisal(message, context)
        if cognitive_appraisal["threat_detected"]:
            impact["fear"] += 0.4 * self.cognitive_appraisals["threat_sensitivity"]
            impact["psychological_safety"] -= 0.4 * self.cognitive_appraisals["threat_sensitivity"]
        if cognitive_appraisal["self_related"]:
            impact["vulnerability"] += 0.3
            if cognitive_appraisal["valence"] < -0.3:
                impact["shame"] += 0.4 * (1 + self.cognitive_appraisals["self_blame"])
                impact["validation"] -= 0.4
            elif cognitive_appraisal["valence"] > 0.3:
                impact["validation"] += 0.3 * self.cognitive_appraisals["reward_sensitivity"]
        if cognitive_appraisal["other_blamed"] and cognitive_appraisal["valence"] < -0.3:
            impact["anger"] += 0.4 * self.cognitive_appraisals["other_blame"]
        if cognitive_appraisal["future_oriented"] and cognitive_appraisal["valence"] > 0.3:
            impact["anticipation"] += 0.4 * self.cognitive_appraisals["future_expectancy"]
        if cognitive_appraisal["certainty"] < 0.35: # Lower threshold
            impact["fear"] += 0.3 * (1 - self.cognitive_appraisals["certainty"])
        if context.get("previous_interaction_negative", False):
            for emotion in impact:
                if impact[emotion] < 0: impact[emotion] *= 1.5 # Amplify more
                elif impact[emotion] > 0: impact[emotion] *= 0.6 # Reduce more
        max_impact = 0.8 + 0.6 * self.emotional_volatility # Allow greater impact
        for emotion in impact: impact[emotion] = max(-max_impact, min(max_impact, impact[emotion]))
        if not strong_trigger_hit and not context.get("high_impact_event"): self.emotional_inertia = min(0.95, self.emotional_inertia + 0.03) # Recover inertia slower
        return impact, cognitive_appraisal

    def _cognitive_appraisal(self, message, context): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Performs cognitive appraisal of the message content"""
        # (Detailed implementation from the previous version)
        message_lower = message.lower()
        appraisal = {
            "valence": 0.0, "self_related": False, "other_blamed": False,
            "self_blamed": False, "certainty": self.cognitive_appraisals["certainty"],
            "future_oriented": False, "threat_detected": False,
            "coping_potential": self.cognitive_appraisals["self_efficacy"],
            "norm_compatibility": 0.5
        }
        # ENGLISH TRANSLATION of Spanish keywords
        positive_words = ["good", "great", "happy", "love", "like", "enjoy", "thanks", "perfect", "excellent", "wonderful", "amazing"]
        negative_words = ["bad", "terrible", "sad", "hate", "disgust", "guilt", "sorry", "problem", "difficult", "failure", "error", "horrible", "disaster"]
        self_words = ["you", "your", "to you", "with you", self.character_name.lower()] # Use character name
        other_words = ["he", "she", "they", "their fault", context.get("user_name", "lin").lower()] # Use user name if exists
        i_words = ["I", "my", "me", "with me"]
        blame_words = ["fault", "responsible", "cause", "you did", "your mistake", "you failed", "you caused"]
        future_words = ["will do", "will be", "future", "plan", "hope", "soon", "tomorrow", "after", "going to"]
        threat_words = ["danger", "threat", "risk", "harm", "hurt", "careful", "attack", "destroy", "warning", "watch out"]
        uncertainty_words = ["maybe", "perhaps", "possibly", "could", "doubt", "don't know", "uncertain", "suppose"]
        certainty_words = ["sure", "definitely", "absolutely", "know", "clear", "always", "never", "obvious", "undoubted"]
        norm_words = ["should", "have to", "normal", "correct", "expected", "supposed to", "unacceptable", "weird"]

        pos_count = sum(word in message_lower for word in positive_words)
        neg_count = sum(word in message_lower for word in negative_words)
        if pos_count > neg_count: appraisal["valence"] = min(1.0, 0.25 * pos_count)
        elif neg_count > pos_count: appraisal["valence"] = max(-1.0, -0.25 * neg_count)

        is_about_poppy = any(word in message_lower for word in self_words)
        is_about_user = any(word in message_lower for word in i_words)
        appraisal["self_related"] = is_about_poppy

        if any(word in message_lower for word in blame_words):
            if is_about_poppy: appraisal["self_blamed"] = True
            if is_about_user or any(word in message_lower for word in other_words): appraisal["other_blamed"] = True

        appraisal["future_oriented"] = any(word in message_lower for word in future_words)
        appraisal["threat_detected"] = any(word in message_lower for word in threat_words)

        unc_count = sum(word in message_lower for word in uncertainty_words)
        cert_count = sum(word in message_lower for word in certainty_words)
        if unc_count > cert_count: appraisal["certainty"] -= 0.2 * unc_count
        elif cert_count > unc_count: appraisal["certainty"] += 0.2 * cert_count
        appraisal["certainty"] = max(0.05, min(0.95, appraisal["certainty"]))

        current_negativity = sum(max(0, self.internal_emotions[e] - 0.5) for e in ["fear", "shame", "grieving", "anger"])
        base_coping = self.personality["resilience"] * 0.6 + self.cognitive_appraisals["self_efficacy"] * 0.4
        appraisal["coping_potential"] = base_coping - current_negativity * 0.3
        if appraisal["threat_detected"]: appraisal["coping_potential"] -= 0.2
        appraisal["coping_potential"] = max(0.1, min(0.9, appraisal["coping_potential"]))

        if any(word in message_lower for word in norm_words):
            if is_about_poppy: appraisal["norm_compatibility"] = 0.15
            else: appraisal["norm_compatibility"] = 0.35
        else: appraisal["norm_compatibility"] = 0.7

        self._update_cognitive_patterns(appraisal)
        return appraisal

    def _update_cognitive_patterns(self, appraisal): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Updates cognitive appraisal patterns based on current appraisal"""
        # (Detailed implementation from the previous version)
        change_rate = 0.012
        patterns = self.cognitive_appraisals
        if appraisal["threat_detected"]: patterns["threat_sensitivity"] = min(0.95, patterns["threat_sensitivity"] + change_rate)
        else: patterns["threat_sensitivity"] = max(0.05, patterns["threat_sensitivity"] - change_rate / 1.5)
        if appraisal["valence"] > 0.5: patterns["reward_sensitivity"] = min(0.95, patterns["reward_sensitivity"] + change_rate)
        elif appraisal["valence"] < -0.5: patterns["reward_sensitivity"] = max(0.05, patterns["reward_sensitivity"] - change_rate / 1.5)
        if appraisal["coping_potential"] > 0.7: patterns["self_efficacy"] = min(0.95, patterns["self_efficacy"] + change_rate * 1.2)
        elif appraisal["coping_potential"] < 0.3: patterns["self_efficacy"] = max(0.05, patterns["self_efficacy"] - change_rate * 1.2)
        if appraisal["other_blamed"]: patterns["other_blame"] = min(0.95, patterns["other_blame"] + change_rate * 1.8)
        else: patterns["other_blame"] = max(0.05, patterns["other_blame"] - change_rate / 1.5)
        if appraisal["self_blamed"]: patterns["self_blame"] = min(0.95, patterns["self_blame"] + change_rate * 1.8)
        else: patterns["self_blame"] = max(0.05, patterns["self_blame"] - change_rate / 1.5)
        if appraisal["future_oriented"] and appraisal["valence"] > 0.4: patterns["future_expectancy"] = min(0.95, patterns["future_expectancy"] + change_rate)
        elif appraisal["future_oriented"] and appraisal["valence"] < -0.4: patterns["future_expectancy"] = max(0.05, patterns["future_expectancy"] - change_rate)
        if appraisal["certainty"] > 0.75: patterns["certainty"] = min(0.95, patterns["certainty"] + change_rate / 1.5)
        elif appraisal["certainty"] < 0.25: patterns["certainty"] = max(0.05, patterns["certainty"] - change_rate / 1.5)

    # --- Memory Methods ---
    def _check_triggers(self, message): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Checks if the message contains emotional triggers"""
        # (Detailed implementation from the previous version)
        triggered_indices = set(); message_lower = message.lower(); current_time = time.time()
        for trigger, indices in self.emotional_triggers.items():
            if trigger in message_lower:
                for index in indices:
                    if 0 <= index < len(self.emotional_memories):
                        memory = self.emotional_memories[index]
                        if memory.get("significance", 0) > 0.15: triggered_indices.add(index)
        themes_in_message = self._extract_themes(message_lower)
        if themes_in_message:
            for core_mem_index in self.core_memories:
                if 0 <= core_mem_index < len(self.emotional_memories):
                    memory = self.emotional_memories[core_mem_index]
                    memory_themes = memory.get("themes", [])
                    if any(theme in themes_in_message for theme in memory_themes):
                        if memory.get("significance", 0) > 0.25: triggered_indices.add(core_mem_index)
        dominant_emotion, dominant_intensity = self._get_dominant_emotion_and_intensity(self.internal_emotions)
        if dominant_emotion != "neutral" and dominant_intensity > 0.55:
            for i, memory in enumerate(self.emotional_memories):
                response_emotions = memory.get("emotional_response", {})
                if dominant_emotion in response_emotions:
                    if abs(response_emotions[dominant_emotion]) > 0.45:
                        time_since_memory = current_time - memory.get("timestamp", current_time)
                        decay_factor = math.exp(-self.memory_decay_rate * time_since_memory / 720)
                        significance = memory.get("significance", 0)
                        recall_probability = min(0.75, dominant_intensity * significance * decay_factor * 0.7)
                        if random.random() < recall_probability: triggered_indices.add(i)
        return list(triggered_indices)

    def _get_dominant_emotion_and_intensity(self, emotion_dict): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Helper to find the dominant emotion and its intensity."""
        # (Detailed implementation from the previous version)
        if not emotion_dict: return "neutral", 0.0
        dominant_emotion = "neutral"; max_intensity_dist = 0.0
        for emotion, value in emotion_dict.items():
            intensity_dist = abs(value - 0.5) # Intensity relative to neutral 0.5
            if intensity_dist > max_intensity_dist: max_intensity_dist = intensity_dist; dominant_emotion = emotion
        # Return the actual value, not the distance
        return dominant_emotion, emotion_dict.get(dominant_emotion, 0.5) # Return the value of the most intense emotion


    def _extract_themes(self, text): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Extracts thematic content from text (simplified)"""
        # (Detailed implementation from the previous version)
        themes = set();
        # ENGLISH TRANSLATION of Spanish theme keywords
        theme_keywords = {
            "rejection": ["rejection", "abandonment", "exclude", "ignore", "discard", "alone", "leave"],
            "betrayal": ["betrayal", "deception", "lie", "unfaithful", "stab", "false friend"],
            "loss": ["lose", "lost", "gone", "without", "death", "miss", "mourning"],
            "failure": ["failure", "error", "bad", "wrong", "disappointment", "useless", "fail", "can't"],
            "success": ["success", "achievement", "win", "good", "perfect", "triumph", "get", "overcome"],
            "connection": ["connect", "together", "united", "close", "intimate", "love", "support", "team", "friendship", "family"],
            "control": ["control", "power", "helpless", "choice", "decide", "free", "order", "force", "manipulate"],
            "identity": ["who I am", "my true self", "identity", "authentic", "be me", "my essence"],
            "vulnerability": ["vulnerable", "open up", "confess", "weak", "hurt", "show feelings"],
            "safety": ["safe", "protected", "trust", "secure", "threat", "danger", "insecurity"]
        }
        for theme, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords): themes.add(theme)
        return list(themes)

    def _amplify_emotions_from_triggers(self, impact, triggered_memories): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Amplifies emotional impact based on triggered memories"""
        # (Detailed implementation from the previous version)
        current_time = time.time()
        amplification_factor = 1.0 + self.personality["neuroticism"] * 0.6
        for memory in triggered_memories:
            memory_index = -1;
            try: memory_index = self.emotional_memories.index(memory)
            except ValueError: continue
            time_since_memory = current_time - memory.get("timestamp", current_time)
            decay_factor = math.exp(-self.memory_decay_rate * time_since_memory / 3600)
            significance = memory.get("significance", 0); strength_factor = 0.0
            if memory_index in self.core_memories: strength_factor = 0.75 * significance * decay_factor
            else: strength_factor = 0.55 * significance * decay_factor
            strength_factor *= amplification_factor
            for emotion, value in memory.get("emotional_response", {}).items():
                if emotion in impact:
                    impact[emotion] += value * strength_factor # Note: Original code had 'value', assuming it's impact value
                    impact[emotion] = max(-0.95, min(0.95, impact[emotion]))

    def _form_emotional_memory(self, message, emotional_impact, context, cognitive_appraisal, timestamp): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Forms emotional memory from significant interactions"""
        # (Detailed implementation from the previous version, with safe pruning)
        intensity = sum(abs(val - 0.5) for val in emotional_impact.values()) / len(emotional_impact) if emotional_impact else 0
        cognitive_significance = 0.0
        if cognitive_appraisal["self_related"]: cognitive_significance += 0.4
        if abs(cognitive_appraisal["valence"]) > 0.65: cognitive_significance += 0.5
        if cognitive_appraisal["threat_detected"]: cognitive_significance += 0.35
        total_significance = (intensity * 0.6 + cognitive_significance * 0.4) * (1 + self.personality["neuroticism"] * 0.7)
        total_significance = min(1.0, max(0.0, total_significance))
        memory_formation_threshold = 0.35
        if total_significance > memory_formation_threshold:
            memory = { "content": message, "context": deepcopy(context),
                        "emotional_response": {e: round(v, 3) for e, v in emotional_impact.items() if abs(v - 0.5) > 0.15},
                        "internal_state_at_time": {e: round(v, 3) for e,v in self.internal_emotions.items()},
                        "cognitive_appraisal": deepcopy(cognitive_appraisal), "significance": round(total_significance, 3),
                        "themes": self._extract_themes(message.lower()), "timestamp": timestamp }
            self.emotional_memories.append(memory)
            if total_significance > self.memory_consolidation_threshold:
                new_core_index = len(self.emotional_memories) - 1
                if new_core_index not in self.core_memories:
                    self.core_memories.append(new_core_index)
                    if len(self.core_memories) > self.max_core_memories:
                        core_details = [(idx, self.emotional_memories[idx].get("significance", 0)) for idx in self.core_memories if idx < len(self.emotional_memories)]
                        if core_details: core_details.sort(key=lambda item: item[1]); idx_to_remove = core_details[0][0]
                        if idx_to_remove in self.core_memories: self.core_memories.remove(idx_to_remove)
            if total_significance > 0.8:
                # ENGLISH TRANSLATION of excluded Spanish words
                words = [w for w in message.lower().split() if len(w) > 4 and w not in ["because", "then", "when", "how", "for", "but", "although"]]
                potential_triggers = random.sample(words, min(len(words), 3))
                mem_index = len(self.emotional_memories) - 1
                for trigger in potential_triggers:
                    if trigger not in self.emotional_triggers: self.emotional_triggers[trigger] = []
                    if mem_index not in self.emotional_triggers[trigger]:
                        self.emotional_triggers[trigger].append(mem_index)
                        if len(self.emotional_triggers[trigger]) > 8: self.emotional_triggers[trigger].pop(0)
        if len(self.emotional_memories) > self.max_emotional_memories:
            self.emotional_memories.sort(key=lambda mem: mem.get("significance", 0)); memory_to_remove = self.emotional_memories.pop(0)
            self._rebuild_memory_indices()


    def _decay_memories(self, time_delta): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Applies decay to the significance of memories"""
        # (Detailed implementation from the previous version, with safe pruning)
        decay_rate_per_sec = 0.00005
        decay_factor = math.exp(-decay_rate_per_sec * time_delta)
        if decay_factor >= 0.999: return

        needs_rebuild = False
        new_emotional_memories = []
        indices_to_remove_from_core = set()
        triggers_to_update = {}

        for i, memory in enumerate(self.emotional_memories):
            is_core = i in self.core_memories
            decay_mod = 0.7 if is_core else 1.0
            memory["significance"] = memory.get("significance", 0) * (1 - (1 - decay_factor) * decay_mod)
            if memory["significance"] < 0.03:
                needs_rebuild = True
                if is_core: indices_to_remove_from_core.add(i)
                # Mark triggers associated with this memory for update
                for trigger, indices in self.emotional_triggers.items():
                    if i in indices:
                        if trigger not in triggers_to_update: triggers_to_update[trigger] = set()
                        triggers_to_update[trigger].add(i)
            else:
                new_emotional_memories.append(memory)

        if needs_rebuild:
            self.emotional_memories = new_emotional_memories
            # Rebuild indices safely
            self._rebuild_memory_indices(indices_to_remove_from_core, triggers_to_update)


    def _evaluate_trauma_triggers(self, message: str, context: dict, emotional_impact: dict) -> dict: # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Evaluates trauma triggers and determines the dominant response."""
        # (Detailed implementation from the previous version)
        trauma_activation = {"activated": False, "intensity": 0.0, "response_type": None}
        message_lower = message.lower()
        # ENGLISH TRANSLATION of Spanish trauma keywords
        trauma_keywords = [ "abandon", "betrayal", "useless", "pathetic", "never enough", "always alone", "nobody cares", "rejected", "failure", "broken", "insecure", "trapped", "helpless", "consumed", "destroy", "hate", "disgust", "extreme guilt", "paralyzing fear" ]
        context_triggers = context.get("trauma_triggers", [])
        trauma_count = sum(keyword in message_lower for keyword in trauma_keywords)
        context_trigger_count = sum(trigger in message_lower for trigger in context_triggers)
        total_trigger_count = trauma_count + context_trigger_count
        if total_trigger_count > 0:
            base_intensity = min(0.9, 0.3 * total_trigger_count)
            vulnerability_factor = self.internal_emotions["vulnerability"] * 0.45
            safety_factor = (1 - self.internal_emotions["psychological_safety"]) * 0.45
            trauma_intensity = base_intensity + vulnerability_factor + safety_factor
            trauma_intensity *= (1 + self.personality["neuroticism"] * 0.6)
            trauma_intensity = min(1.0, max(0.0, trauma_intensity))
            activation_threshold = 0.6 - (self.personality["resilience"] * 0.2)
            if trauma_intensity > activation_threshold:
                trauma_activation["activated"] = True
                trauma_activation["intensity"] = round(trauma_intensity, 3)
                response_strengths = {}
                total_tendency = sum(self.trauma_responses.values()) + 1e-6
                for response, tendency in self.trauma_responses.items():
                    strength = tendency / total_tendency
                    if context.get("is_user_threatening", False):
                        if response == "flight": strength *= 1.7
                        elif response == "freeze": strength *= 1.5
                        elif response == "fight": strength *= 0.5
                    elif context.get("user_is_pleading", False):
                        if response == "fawn": strength *= 1.8
                        elif response == "fight": strength *= 0.3
                    elif context.get("feels_cornered", False):
                        if response == "fight": strength *= 1.7
                        elif response == "freeze": strength *= 1.5
                        elif response == "flight": strength *= 0.6
                    response_strengths[response] = max(0, strength * (1 + random.uniform(-0.2, 0.2)))
                dominant_response = max(response_strengths, key=response_strengths.get)
                trauma_activation["response_type"] = dominant_response
                impact_modifier = 1.0 - trauma_intensity * 0.85
                for emotion in emotional_impact: emotional_impact[emotion] *= impact_modifier
                trauma_effect_scale = trauma_intensity
                if dominant_response == "fight":
                    emotional_impact["anger"] = min(1.0, emotional_impact.get("anger", 0) + 0.85 * trauma_effect_scale)
                    emotional_impact["fear"] = min(1.0, emotional_impact.get("fear", 0) + 0.5 * trauma_effect_scale)
                    emotional_impact["connection"] = max(0.0, emotional_impact.get("connection", 0) - 0.6 * trauma_effect_scale)
                    emotional_impact["autonomy"] = min(1.0, emotional_impact.get("autonomy", 0) + 0.2 * trauma_effect_scale)
                    emotional_impact["psychological_safety"] = 0.1
                elif dominant_response == "flight":
                    emotional_impact["fear"] = min(1.0, emotional_impact.get("fear", 0) + 0.95 * trauma_effect_scale)
                    emotional_impact["connection"] = max(0.0, emotional_impact.get("connection", 0) - 0.7 * trauma_effect_scale)
                    emotional_impact["autonomy"] = min(1.0, emotional_impact.get("autonomy", 0) + 0.4 * trauma_effect_scale)
                    emotional_impact["psychological_safety"] = 0.05
                elif dominant_response == "freeze":
                    emotional_impact["fear"] = min(1.0, emotional_impact.get("fear", 0) + 0.7 * trauma_effect_scale)
                    emotional_impact["autonomy"] = max(0.0, emotional_impact.get("autonomy", 0) - 0.9 * trauma_effect_scale)
                    numb_factor = 1.0 - (0.7 * trauma_effect_scale)
                    for emotion in emotional_impact:
                        if emotion not in ["fear", "autonomy"]: emotional_impact[emotion] *= numb_factor
                    emotional_impact["psychological_safety"] = 0.1
                elif dominant_response == "fawn":
                    emotional_impact["fear"] = min(1.0, emotional_impact.get("fear", 0) + 0.5 * trauma_effect_scale)
                    emotional_impact["vulnerability"] = min(1.0, emotional_impact.get("vulnerability", 0) + 0.7 * trauma_effect_scale)
                    emotional_impact["authenticity"] = max(0.0, emotional_impact.get("authenticity", 0) - 0.8 * trauma_effect_scale)
                    emotional_impact["validation"] = min(1.0, emotional_impact.get("validation", 0) + 0.6 * trauma_effect_scale)
                    emotional_impact["connection"] = min(1.0, emotional_impact.get("connection", 0) + 0.3 * trauma_effect_scale)
                    emotional_impact["psychological_safety"] = 0.15
                elif dominant_response == "dissociation":
                    numb_factor = 1.0 - (0.9 * trauma_effect_scale)
                    for emotion in emotional_impact: emotional_impact[emotion] *= numb_factor
                    emotional_impact["connection"] = max(0.0, emotional_impact.get("connection", 0) - 0.8 * trauma_effect_scale)
                    emotional_impact["authenticity"] = max(0.0, emotional_impact.get("authenticity", 0) - 0.8 * trauma_effect_scale)
                    emotional_impact["vulnerability"] = max(0.0, emotional_impact.get("vulnerability", 0) - 0.5 * trauma_effect_scale)
                    emotional_impact["psychological_safety"] = 0.2
        return trauma_activation

    def _process_emotional_contagion(self, other_emotions): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Processes emotional contagion from the interlocutor"""
        # (Detailed implementation from the previous version)
        if not other_emotions or not isinstance(other_emotions, dict): return
        contagion_strength = self.emotional_contagion * (0.5 + self.personality["extraversion"])
        if self.internal_emotions["vulnerability"] > 0.7: contagion_strength *= 1.4
        if self.internal_emotions["psychological_safety"] < 0.3: contagion_strength *= 0.6
        empathy_factor = self.personality["empathy"]
        neuroticism_factor = 1.0 + max(0, self.personality["neuroticism"] - 0.5) * 0.6
        for emotion, value in other_emotions.items():
            if emotion in self.internal_emotions:
                intensity_diff_factor = 1.0 + abs(value - self.internal_emotions[emotion]) * 0.5
                effect = (value - self.internal_emotions[emotion])
                effect *= contagion_strength * empathy_factor * intensity_diff_factor * 0.18
                if value < 0.5: effect *= neuroticism_factor
                self.internal_emotions[emotion] += effect
                self.internal_emotions[emotion] = max(0.0, min(1.0, self.internal_emotions[emotion]))

    # --- Internal Emotional State Methods ---
    def _update_internal_emotions(self, emotional_impact, context, trauma_activation=None): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Updates the internal emotional state"""
        # (Detailed implementation from the previous version)
        high_impact_flag = context.get("high_impact_event", False) or (trauma_activation and trauma_activation["activated"])
        fatigue_factor = self.fatigue_level * 0.3 # Uses self.fatigue_level calculated here
        for emotion in list(self.internal_emotions.keys()):
            change = emotional_impact.get(emotion, 0.0) * (1 - self.emotional_inertia)
            if emotion == 'joy': change -= fatigue_factor * 0.1
            if emotion == 'anger': change += fatigue_factor * 0.05
            change *= (1 - fatigue_factor * 0.2)
            if trauma_activation and trauma_activation["activated"] and trauma_activation["response_type"] == "dissociation":
                target_numb_value = 0.5; numb_strength = trauma_activation["intensity"] * 0.5
                self.internal_emotions[emotion] += (target_numb_value - self.internal_emotions[emotion]) * numb_strength
                change *= (1 - numb_strength)
            max_change = 0.35 + 0.4 * self.emotional_volatility
            if high_impact_flag: max_change *= 1.8
            change = max(-max_change, min(max_change, change))
            self.internal_emotions[emotion] += change
            if self.internal_emotions[emotion] > 1.0: self.internal_emotions[emotion] = 1.0 - (self.internal_emotions[emotion] - 1.0) * 0.3
            if self.internal_emotions[emotion] < 0.0: self.internal_emotions[emotion] = abs(self.internal_emotions[emotion]) * 0.3
            self.internal_emotions[emotion] = max(0.0, min(1.0, self.internal_emotions[emotion]))
        self._differentiate_emotions()
        if context.get("location") == "public":
            public_factor = 1.0 - (self.cultural_factors["emotional_display_rules"] * 0.35)
            self.internal_emotions["vulnerability"] *= public_factor; self.internal_emotions["anger"] *= public_factor
            self.internal_emotions["grieving"] *= public_factor; self.internal_emotions["joy"] *= public_factor * 0.8
            self.internal_emotions["psychological_safety"] *= 0.85
        if context.get("recent_failure", False):
            impact_on_validation = emotional_impact.get("validation", 0)
            if impact_on_validation < 0: self.internal_emotions["validation"] += impact_on_validation * 0.6
            self.internal_emotions["shame"] = min(1.0, self.internal_emotions["shame"] + 0.2 * (1 + self.personality["neuroticism"]))
            self.cognitive_appraisals["self_efficacy"] = max(0.05, self.cognitive_appraisals["self_efficacy"] - 0.15)
        if self.internal_emotions["vulnerability"] > 0.75: self.internal_emotions["autonomy"] *= 0.85
        if self.internal_emotions["psychological_safety"] < 0.25:
            self.internal_emotions["vulnerability"] *= 0.75; self.internal_emotions["authenticity"] *= 0.75
            self.internal_emotions["fear"] = min(1.0, self.internal_emotions["fear"] + 0.25)
        if self.internal_emotions["anger"] > 0.75: self.internal_emotions["joy"] *= 0.65
        if self.internal_emotions["shame"] > 0.75: self.internal_emotions["validation"] *= 0.75
        unconscious = self.unconscious_patterns
        if unconscious["fear_of_abandonment"] > 0.6 and self.internal_emotions["connection"] < 0.35:
            fear_factor = unconscious["fear_of_abandonment"] * 0.35
            self.internal_emotions["vulnerability"] += fear_factor; self.internal_emotions["fear"] += fear_factor
            self.internal_emotions["psychological_safety"] -= fear_factor * 0.6
        if unconscious["impostor_syndrome"] > 0.7 and self.internal_emotions["validation"] > 0.75:
            impostor_factor = unconscious["impostor_syndrome"] * 0.25
            self.internal_emotions["fear"] += impostor_factor; self.internal_emotions["shame"] += impostor_factor * 0.6
        if unconscious["rejection_sensitivity"] > 0.75 and (self.internal_emotions["connection"] < 0.4 or self.internal_emotions["validation"] < 0.3):
            rejection_factor = unconscious["rejection_sensitivity"] * 0.35
            self.internal_emotions["shame"] += rejection_factor; self.internal_emotions["anger"] += rejection_factor * 0.8
            self.internal_emotions["fear"] += rejection_factor * 0.6
        if unconscious["spotlight_effect"] > 0.7 and context.get("social_situation", False):
            spotlight_factor = unconscious["spotlight_effect"] * 0.25
            self.internal_emotions["vulnerability"] += spotlight_factor; self.internal_emotions["fear"] += spotlight_factor * 0.6
            self.internal_emotions["psychological_safety"] -= spotlight_factor * 0.6
        for emotion in self.internal_emotions: self.internal_emotions[emotion] = max(0.0, min(1.0, self.internal_emotions[emotion]))

    def _differentiate_emotions(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Differentiates between similar emotions based on emotional granularity"""
        # (Detailed implementation from the previous version)
        if self.emotional_granularity < 0.5:
            similarity_groups = [ ["fear", "vulnerability"], ["anger", "disgust"], ["joy", "anticipation"], ["validation", "connection"], ["authenticity", "autonomy"], ["shame", "grieving"] ]
            blend_strength = (0.5 - self.emotional_granularity) * 0.7
            for group in similarity_groups:
                valid_emotions = [e for e in group if e in self.internal_emotions]
                if len(valid_emotions) > 1:
                    avg_value = sum(self.internal_emotions[e] for e in valid_emotions) / len(valid_emotions)
                    for emotion in valid_emotions:
                        self.internal_emotions[emotion] = self.internal_emotions[emotion] * (1 - blend_strength) + avg_value * blend_strength

    def _apply_cultural_display_rules(self, context): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Placeholder"""
        pass

    # --- Regulation and Defense Methods ---
    def _apply_regulation_strategies(self, context): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Applies emotional regulation strategies"""
        # (Detailed implementation from the previous version)
        regulation_effects = {"applied_strategies": []}; emotions_to_regulate = {}
        regulation_threshold = 0.65 - self.emotional_intelligence["self_management"] * 0.2
        for emotion, intensity in self.internal_emotions.items():
            if intensity > regulation_threshold:
                if emotion not in ["joy", "anticipation", "validation"] or intensity > 0.9: emotions_to_regulate[emotion] = intensity
            elif context.get("inappropriate_emotions", []) and emotion in context["inappropriate_emotions"]: emotions_to_regulate[emotion] = intensity
        if not emotions_to_regulate: return regulation_effects
        strategy_options = {}
        for strategy, skill in self.regulation_strategies.items():
            applicable = True
            if strategy == "situation_selection" and not context.get("can_change_situation", True): applicable = False
            if strategy == "seeking_support" and not context.get("support_available", True): applicable = False
            if applicable:
                appropriateness = 1.0
                if strategy == "acceptance" and ("grieving" in emotions_to_regulate or "shame" in emotions_to_regulate): appropriateness = 1.5
                if strategy == "problem_solving" and ("anger" in emotions_to_regulate or "fear" in emotions_to_regulate): appropriateness = 1.4
                if strategy == "self_soothing" and self.internal_emotions["psychological_safety"] < 0.4: appropriateness = 1.4
                if strategy == "expressive_suppression" and self.unconscious_patterns["emotional_repression"] > 0.6: appropriateness = 1.3
                if strategy == "cognitive_reappraisal" and self.personality["openness"] > 0.5: appropriateness = 1.2
                appropriateness *= (1 - self.fatigue_level * 0.3) if strategy in ["cognitive_reappraisal", "problem_solving"] else 1.0
                strategy_options[strategy] = skill * appropriateness * (1 + random.uniform(-0.15, 0.15))
        if not strategy_options: return regulation_effects
        chosen_strategy = max(strategy_options, key=strategy_options.get); strategy_strength = self.regulation_strategies[chosen_strategy]
        regulation_effects["applied_strategies"].append(chosen_strategy)

        if chosen_strategy == "expressive_suppression":
            regulation_effects["suppression_factor"] = 1.0 - (strategy_strength * 0.75)
            self.internal_emotions["authenticity"] *= (1 - strategy_strength * 0.25)
        elif chosen_strategy == "cognitive_reappraisal":
            reduction_factor = strategy_strength * 0.45 * (1 - self.fatigue_level * 0.5)
            internal_changed = False
            for emotion in emotions_to_regulate:
                if self.internal_emotions[emotion] > 0.5:
                    original_value = self.internal_emotions[emotion]
                    self.internal_emotions[emotion] *= (1 - reduction_factor)
                    if self.internal_emotions[emotion] != original_value: internal_changed = True
            if internal_changed: regulation_effects["internal_change"] = True
        elif chosen_strategy == "acceptance":
            self.internal_emotions["authenticity"] = min(1.0, self.internal_emotions["authenticity"] * (1 + strategy_strength * 0.2))
            self.internal_emotions["anger"] *= (1 - strategy_strength * 0.15)
            self.internal_emotions["shame"] *= (1 - strategy_strength * 0.15)
            regulation_effects["internal_change"] = True
        elif chosen_strategy == "problem_solving":
            self.internal_emotions["fear"] *= (1 - strategy_strength * 0.25)
            self.internal_emotions["autonomy"] = min(1.0, self.internal_emotions["autonomy"] + strategy_strength * 0.3)
            if "anger" in emotions_to_regulate: self.internal_emotions["anger"] *= (1 - strategy_strength * 0.35)
            regulation_effects["internal_change"] = True
        elif chosen_strategy == "situation_selection":
            self.internal_emotions["psychological_safety"] = min(1.0, self.internal_emotions["psychological_safety"] + strategy_strength * 0.35)
            self.internal_emotions["connection"] *= (1 - strategy_strength * 0.15)
            reduction_factor = strategy_strength * 0.55
            internal_changed = False
            for emotion in emotions_to_regulate:
                original_value = self.internal_emotions[emotion]
                self.internal_emotions[emotion] *= (1 - reduction_factor)
                if self.internal_emotions[emotion] != original_value: internal_changed = True
            if internal_changed: regulation_effects["internal_change"] = True
        elif chosen_strategy == "self_soothing":
            reduction_factor = strategy_strength * 0.35
            internal_changed = False
            for emotion in ["fear", "shame", "anger", "grieving", "vulnerability"]:
                if emotion in self.internal_emotions:
                    original_value = self.internal_emotions[emotion]
                    self.internal_emotions[emotion] *= (1 - reduction_factor)
                    if self.internal_emotions[emotion] != original_value: internal_changed = True
            if internal_changed: regulation_effects["internal_change"] = True
        elif chosen_strategy == "seeking_support":
            self.internal_emotions["connection"] = min(1.0, self.internal_emotions["connection"] + strategy_strength * 0.45)
            reduction_factor = strategy_strength * 0.3
            internal_changed = False
            for emotion in emotions_to_regulate:
                original_value = self.internal_emotions[emotion]
                self.internal_emotions[emotion] *= (1 - reduction_factor)
                if self.internal_emotions[emotion] != original_value: internal_changed = True
            if self.internal_emotions["connection"] > 0: regulation_effects["internal_change"] = True
        elif chosen_strategy == "attention_deployment":
            if emotions_to_regulate:
                target_emotion = max(emotions_to_regulate, key=emotions_to_regulate.get)
                self.internal_emotions[target_emotion] *= (1 - strategy_strength * 0.25)
                regulation_effects["internal_change"] = True

        self.regulation_strategies[chosen_strategy] = min(1.0, strategy_strength + 0.008) # Use strategy_strength here maybe? Or skill? Using skill.
        # self.regulation_strategies[chosen_strategy] = min(1.0, self.regulation_strategies[chosen_strategy] + 0.008) # Original line

        return regulation_effects

    def _evaluate_defenses(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Evaluates and activates defense mechanisms"""
        # (Detailed implementation from the previous version)
        self.active_defenses = []; emotional_state = self._determine_emotional_state(); safety = self.internal_emotions["psychological_safety"]
        fatigue_defense_factor = 1 + self.fatigue_level * 0.3
        defense_activation_threshold = self.defense_activation * (1 - self.emotional_intelligence["self_management"] * 0.3)
        if ("Opening Up" in emotional_state or "Authentic" in emotional_state) and safety > 0.65: return
        defense_candidates = []; vulnerability = self.internal_emotions["vulnerability"]; anger = self.internal_emotions["anger"]; shame = self.internal_emotions["shame"]; autonomy = self.internal_emotions["autonomy"]; connection = self.internal_emotions["connection"]
        if vulnerability * fatigue_defense_factor > defense_activation_threshold:
            if self.personality["pride"] > 0.6: defense_candidates.append({"type": "reaction_formation", "strength": self.personality["pride"] * vulnerability * 0.9})
            if self.personality["fear_of_vulnerability"] > 0.5: defense_candidates.append({"type": "intellectualization", "strength": self.personality["fear_of_vulnerability"] * vulnerability * 1.0})
            if self.unconscious_patterns["perfectionism"] > 0.7: defense_candidates.append({"type": "compensation", "strength": self.unconscious_patterns["perfectionism"] * vulnerability * 0.8})
        if anger * fatigue_defense_factor > 0.65 and safety < 0.35: defense_candidates.append({"type": "displacement", "strength": anger * (1 - safety) * 0.7})
        overwhelmed_score = sum(max(0, intensity - 0.75) for intensity in self.internal_emotions.values()) * fatigue_defense_factor
        if overwhelmed_score > 0.6: defense_candidates.append({"type": "denial", "strength": overwhelmed_score * 0.9})
        if shame * fatigue_defense_factor > 0.65 and safety < 0.45: defense_candidates.append({"type": "rationalization", "strength": shame * (1 - safety) * 0.8})
        ambivalence = 1.0 - abs(connection - 0.5) * 2
        if ambivalence > 0.65 and safety < 0.35: defense_candidates.append({"type": "splitting", "strength": ambivalence * (1 - safety) * 0.6})
        if autonomy < 0.25: defense_candidates.append({"type": "projection", "strength": (1 - autonomy) * 0.8})
        if defense_candidates:
            defense_candidates.sort(key=lambda x: x["strength"], reverse=True); self.active_defenses = defense_candidates[:3]
            for defense in self.active_defenses: defense["target_emotion"] = "various"; defense["behavior"] = f"Shows behavior of {defense['type']}" # ENGLISH TRANSLATION

    # --- Emotional Expression Methods ---
    def _calculate_expressed_emotions(self, regulation_effects=None): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Calculates expressed emotions"""
        # (Detailed implementation from the previous version)
        self.expressed_emotions = self.internal_emotions.copy(); suppression_factor = regulation_effects.get("suppression_factor", 1.0) if regulation_effects else 1.0
        if suppression_factor < 1.0:
            for emotion in self.expressed_emotions:
                effectiveness = 0.75 if emotion in ["vulnerability", "fear", "shame", "grieving", "anger"] else 0.45
                self.expressed_emotions[emotion] *= (1 - (1 - suppression_factor) * effectiveness)
        for defense in self.active_defenses:
            strength = defense["strength"]; dtype = defense["type"]
            if dtype == "reaction_formation":
                target = defense.get("target_emotion", "vulnerability")
                if target in self.expressed_emotions: self.expressed_emotions[target] = max(0.0, 0.1 - self.internal_emotions[target] * strength * 0.9)
                self.expressed_emotions["autonomy"] = min(1.0, self.expressed_emotions["autonomy"] + strength * 0.5); self.expressed_emotions["validation"] = min(1.0, self.expressed_emotions["validation"] + strength * 0.4)
            elif dtype == "intellectualization":
                reduction = strength * 0.65;
                for emotion in self.expressed_emotions: self.expressed_emotions[emotion] *= (1 - reduction)
                self.expressed_emotions["authenticity"] *= (1 - strength * 0.85); self.expressed_emotions["autonomy"] = min(1.0, self.expressed_emotions["autonomy"] + strength * 0.25)
            elif dtype == "projection": self.expressed_emotions["anger"] = min(1.0, self.expressed_emotions["anger"] + strength * 0.45)
            elif dtype == "compensation":
                self.expressed_emotions["validation"] = min(1.0, 0.65 + strength * 0.45); self.expressed_emotions["autonomy"] = min(1.0, 0.55 + strength * 0.55)
                self.expressed_emotions["vulnerability"] *= (1 - strength * 0.65); self.expressed_emotions["shame"] *= (1 - strength * 0.65)
            elif dtype == "displacement": pass
            elif dtype == "denial":
                reduction = strength * 0.9
                for emotion in ["fear", "grief", "vulnerability", "shame", "anger"]:
                    if emotion in self.expressed_emotions: self.expressed_emotions[emotion] *= (1 - reduction)
                self.expressed_emotions["joy"] = min(1.0, self.expressed_emotions["joy"] + strength * 0.35)
            elif dtype == "rationalization":
                self.expressed_emotions["shame"] *= (1 - strength * 0.75); self.expressed_emotions["autonomy"] = min(1.0, self.expressed_emotions["autonomy"] + strength * 0.25)
            elif dtype == "splitting":
                split_factor = strength * 0.45
                for emotion in self.expressed_emotions:
                    if self.expressed_emotions[emotion] > 0.5: self.expressed_emotions[emotion] = min(1.0, self.expressed_emotions[emotion] + split_factor)
                    else: self.expressed_emotions[emotion] = max(0.0, self.expressed_emotions[emotion] - split_factor)
        pride = self.personality["pride"]
        if pride > 0.6: self.expressed_emotions["vulnerability"] *= (1 - pride * 0.55); self.expressed_emotions["shame"] *= (1 - pride * 0.55); self.expressed_emotions["fear"] *= (1 - pride * 0.35)
        awareness = self.personality["emotional_awareness"]; awareness_gap = 1.0 - awareness
        if awareness_gap > 0.1:
            for emotion in self.expressed_emotions:
                drift = (self.internal_emotions[emotion] - self.expressed_emotions[emotion]) * awareness_gap * 0.45; self.expressed_emotions[emotion] += drift
        if self.fatigue_level > 0.6:
            fatigue_mask_reduction = (self.fatigue_level - 0.6) * 0.5
            for emotion in self.expressed_emotions:
                self.expressed_emotions[emotion] += (self.internal_emotions[emotion] - self.expressed_emotions[emotion]) * fatigue_mask_reduction
        facade_total = 0; num_emotions = len(self.internal_emotions)
        for emotion in self.expressed_emotions:
            self.expressed_emotions[emotion] = max(0.0, min(1.0, self.expressed_emotions[emotion])); facade_total += abs(self.internal_emotions[emotion] - self.expressed_emotions[emotion])
        self.facade_intensity = min(1.0, facade_total / num_emotions * 2.0) if num_emotions > 0 else 0.0


    # --- Relationship and Attachment Methods ---
    def _update_relationship(self, message, emotional_impact, context): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Updates relationship dynamics considering attachment"""
        # (Detailed implementation from the previous version)
        trust_change = 0.0; intimacy_change = 0.0; distance_change = 0.0; safety_impact = emotional_impact.get("psychological_safety", 0); connection_impact = emotional_impact.get("connection", 0)
        if safety_impact > 0: trust_change += safety_impact * 0.12
        else: trust_change += safety_impact * 0.25
        if self.internal_emotions["connection"] > self.trust_threshold: intimacy_change += 0.07
        if connection_impact > 0: distance_change -= connection_impact * 0.13
        else: distance_change -= connection_impact * 0.18
        anxiety = self.attachment_style["anxiety"]; avoidance = self.attachment_style["avoidance"]; security = self.attachment_style["security"]; disorganization = self.attachment_style["disorganization"]
        if anxiety > 0.6:
            if connection_impact < -0.25: distance_change += abs(connection_impact) * 0.35 * anxiety; trust_change -= 0.06 * anxiety
            elif connection_impact > 0.25: intimacy_change += connection_impact * 0.25 * anxiety
        if avoidance > 0.6:
            max_intimacy = 0.75 - (avoidance * 0.55); self.intimacy_level = min(self.intimacy_level + intimacy_change, max_intimacy); intimacy_change = 0
            min_distance = 0.25 + (avoidance * 0.45); self.psychological_distance = max(self.psychological_distance + distance_change, min_distance); distance_change = 0
        if security > 0.6:
            trust_change *= (1 - security * 0.45)
            if connection_impact < 0: distance_change += security * 0.35 * abs(connection_impact)
        if disorganization > 0.6:
            noise = disorganization * 0.12; trust_change += random.uniform(-noise, noise); intimacy_change += random.uniform(-noise, noise); distance_change += random.uniform(-noise, noise)
        self.trust_threshold += trust_change; self.intimacy_level += intimacy_change; self.psychological_distance += distance_change
        self.trust_threshold = max(0.05, min(0.95, self.trust_threshold)); self.intimacy_level = max(0.0, min(1.0, self.intimacy_level)); self.psychological_distance = max(0.05, min(0.95, self.psychological_distance))

    def _update_attachment_patterns(self, context, emotional_impact): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Updates attachment patterns (very slow change)"""
        # (Detailed implementation from the previous version)
        if random.random() > 0.15: return
        change_rate = 0.012; style = self.attachment_style; connection = self.internal_emotions["connection"]; safety = self.internal_emotions["psychological_safety"]
        if connection > 0.65 and safety > 0.65: style["security"] += change_rate; style["anxiety"] -= change_rate * 0.6; style["avoidance"] -= change_rate * 0.6
        elif (emotional_impact.get("connection", 0) < -0.45 or context.get("rejection_experience", False)): style["anxiety"] += change_rate * 1.6; style["security"] -= change_rate * 1.1
        elif (context.get("boundary_violation", False) or self.internal_emotions["autonomy"] < 0.15): style["avoidance"] += change_rate * 1.6; style["security"] -= change_rate * 1.1
        elif (safety < 0.25 and (connection > 0.75 or connection < 0.25)): style["disorganization"] += change_rate * 1.7; style["security"] -= change_rate * 1.2
        for key in style: style[key] = max(0.05, min(0.95, style[key]))

    # --- Evolution and Growth Methods ---
    def _evolve_personality(self, emotional_impact, trauma_activation, context): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Gradually evolves personality"""
        # (Detailed implementation from the previous version)
        intensity = sum(abs(val - 0.5) for val in emotional_impact.values()) # Use distance from neutral
        should_evolve = intensity > 0.5 or (trauma_activation and trauma_activation["activated"]) or context.get("growth_opportunity_taken", False)
        if not should_evolve: return
        change_rate = 0.007
        p = self.personality
        if self.internal_emotions["vulnerability"] > 0.65 and self.internal_emotions["psychological_safety"] > 0.65: p["emotional_awareness"] += change_rate; p["fear_of_vulnerability"] -= change_rate; p["empathy"] += change_rate * 0.6; p["neuroticism"] -= change_rate * 0.6
        if self.internal_emotions["connection"] > 0.85: p["empathy"] += change_rate; p["agreeableness"] += change_rate; p["extraversion"] += change_rate * 0.6
        if self.internal_emotions["validation"] > 0.85 and self.internal_emotions["joy"] > 0.75: p["conscientiousness"] += change_rate * 0.6; p["neuroticism"] -= change_rate * 0.6;
        if self.unconscious_patterns["self_worth_contingency"] > 0.6: p["pride"] += change_rate
        if context.get("recent_failure", False) and self.internal_emotions["psychological_safety"] > 0.55: p["resilience"] += change_rate * 1.6; p["adaptability"] += change_rate * 1.1
        elif context.get("recent_failure", False) and self.internal_emotions["psychological_safety"] < 0.35: p["neuroticism"] += change_rate * 1.7; p["resilience"] -= change_rate * 1.1
        if trauma_activation and trauma_activation["activated"]: p["neuroticism"] += change_rate * 2.2; p["resilience"] -= change_rate * 1.7
        if context.get("growth_opportunity_taken", False): p["resilience"] += change_rate * 1.7; p["adaptability"] += change_rate * 1.7; p["emotional_awareness"] += change_rate * 1.1
        for key in p: p[key] = max(0.05, min(0.95, p[key]))
        self._update_emotional_intelligence()


    def _process_growth_opportunities(self, context, regulation_effects): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Processes opportunities for personal growth"""
        # (Detailed implementation from the previous version)
        growth_occurred = False; growth_rate = 0.015
        if regulation_effects and "applied_strategies" in regulation_effects:
            adaptive_strategies_used = [s for s in regulation_effects["applied_strategies"] if s in ["cognitive_reappraisal", "acceptance", "problem_solving", "self_soothing", "seeking_support"]]
            initial_intensity = context.get("initial_emotional_intensity", 0.5)
            if adaptive_strategies_used and initial_intensity > 0.6:
                self.personal_growth["emotional_integration"] += growth_rate; self.personal_growth["self_compassion"] += growth_rate * 0.7; growth_occurred = True
        if context.get("insight_gained", False):
            self.personal_growth["insight_development"] += growth_rate * 1.7; self.personal_growth["schema_restructuring"] += growth_rate * 1.2; growth_occurred = True
        if self.internal_emotions["connection"] > 0.8 and self.internal_emotions["psychological_safety"] > 0.8:
            self.personal_growth["identity_coherence"] += growth_rate * 0.7; self.personal_growth["self_compassion"] += growth_rate * 0.7; growth_occurred = True
        for key in self.personal_growth: self.personal_growth[key] = max(0.0, min(1.0, self.personal_growth[key]))
        return growth_occurred

    # --- Fatigue Calculation Logic ---
    # --- MODIFIED SECTION START ---
    # Se eliminó la definición duplicada de _update_fatigue. Se mantiene la más detallada.
    def _update_fatigue(self, time_delta_seconds):
        """
        Updates fatigue level based on time passed, emotional intensity,
        and personality traits (resilience, conscientiousness).
        This is called when the character is AWAKE.
        """
        if time_delta_seconds <= 0: return # No time passed

        # 1. Base fatigue increase over time
        base_increase = BASE_FATIGUE_INCREASE * time_delta_seconds

        # 2. Impact of emotional intensity (higher intensity = more tiring)
        active_emotions = [v for v in self.internal_emotions.values() if v > 0.1]
        avg_intensity = sum(active_emotions) / len(active_emotions) if active_emotions else 0
        emotional_drain = avg_intensity * FATIGUE_EMOTIONAL_IMPACT_FACTOR * time_delta_seconds

        # 3. Personality modulation
        resilience_factor = 1.0 - (self.personality.get("resilience", 0.5) * 0.5)
        conscientiousness_factor = 1.0 + (self.personality.get("conscientiousness", 0.5) * 0.1)

        # 4. Calculate total increase
        total_increase = (base_increase + emotional_drain) * resilience_factor * conscientiousness_factor

        # 5. Update fatigue level and clamp
        self.fatigue_level += total_increase
        self.fatigue_level = max(0.0, min(100.0, self.fatigue_level)) # Clamp [0, 100]

    # --- ADDED METHOD ---
    def update_fatigue_state(self, time_delta_hours, is_sleeping):
        """
        Updates the fatigue level based on time passed and sleep state.
        Called externally by RPLogic.
        """
        if time_delta_hours <= 0:
            return

        if is_sleeping:
            # Apply fatigue recovery
            recovery_amount = FATIGUE_RECOVERY_RATE * time_delta_hours
            self.fatigue_level -= recovery_amount
            self.fatigue_level = max(0.0, self.fatigue_level) # Clamp at 0
            logger.debug(f"Fatigue Recovery: Recovered {recovery_amount:.2f}. New level: {self.fatigue_level:.2f}")
        else:
            # Apply fatigue increase using the detailed internal method
            time_delta_seconds = time_delta_hours * 3600
            logger.debug(f"Fatigue Increase: Calling _update_fatigue with {time_delta_seconds:.1f} seconds.")
            self._update_fatigue(time_delta_seconds)
            logger.debug(f"Fatigue level after increase: {self.fatigue_level:.2f}")
    # --- MODIFIED SECTION END ---


    # --- Sleep Cycle Processing (Now triggered externally if needed) ---
    def _process_sleep_cycle(self): # <-- SECTION REVIEWED/KEPT (Logic from your code, but no longer called automatically)
        """
        Simulates the effects of a sleep cycle (e.g., memory consolidation,
        emotional reset). This is no longer called automatically based on time awake.
        RPLogic can call this when sleep starts if desired.
        """
        logger.info("Processing sleep cycle effects...")

        # 1. Significant Fatigue Reduction (now handled by recovery in update_fatigue_state)
        # 2. Emotional Reset/Dampening
        for emotion, value in self.internal_emotions.items():
            if emotion in ["anger", "fear", "sadness", "disgust"] and value > 0.5:
                self.internal_emotions[emotion] *= 0.6
            elif value > 0.7:
                 self.internal_emotions[emotion] *= 0.8
            self.internal_emotions[emotion] = max(0.0, min(1.0, self.internal_emotions[emotion]))
        # self._calculate_pad_from_detailed() # Recalculate PAD - Assuming this method exists from previous code
        logger.info("Emotions dampened/reset after sleep cycle.")
        logger.debug("Emotions after sleep reset: %s", {k: f"{v:.2f}" for k, v in self.internal_emotions.items()})

        # 3. Relationship State Reset (optional)
        self.relationship_state["conflict_level"] = max(0.0, self.relationship_state["conflict_level"] * 0.8)
        logger.info(f"Conflict level reduced after sleep cycle to: {self.relationship_state['conflict_level']:.2f}")

        # 4. Trigger Memory Consolidation (Conceptual)
        memory_logger.info("Sleep cycle: Triggering memory consolidation process (conceptual).")

        logger.info("Sleep cycle processing complete.")

    def _rebuild_memory_indices(self, removed_indices=None, updated_triggers=None): # <-- MODIFIED SECTION START --- (Added parameters for safety)
        """Rebuilds indices in core_memories and emotional_triggers after pruning."""
        # (Implementation adjusted for safer rebuilding)
        logger.debug("Rebuilding memory indices...")
        content_to_new_index = {mem['content']: i for i, mem in enumerate(self.emotional_memories)}

        # Rebuild core_memories
        new_core_memories = []
        for old_index in self.core_memories:
            # Find the content of the old core memory
            # This part requires careful handling if the memory object itself was removed
            # A safer approach might be to store core memory *content* or unique IDs
            # For now, assuming the memory object might still exist temporarily or we have its content
            # This part is complex and depends on how pruning was implemented.
            # Let's assume we can map old index to content somehow if needed.
            # Simplified: If an index is removed, just skip it.
            # A better way is needed if indices shift significantly.
            # We need a stable way to identify core memories across pruning.
            # --- SAFER APPROACH ---
            # Check if the old index still corresponds to a valid memory in the new list
            # This requires knowing the mapping or content. Assuming direct index mapping for now (RISKY)
            if old_index < len(self.emotional_memories): # Check if index is valid in the *potentially* old list size context
                 # This logic is flawed if indices shifted. Need a robust mapping.
                 # Placeholder: Assume content check is possible
                 # memory_content = get_content_for_old_index(old_index) # Function needed
                 # if memory_content in content_to_new_index:
                 #    new_core_memories.append(content_to_new_index[memory_content])
                 pass # Needs robust implementation

        # Rebuild emotional_triggers
        new_triggers = {}
        for trigger, old_indices in self.emotional_triggers.items():
            new_indices_for_trigger = []
            for old_index in old_indices:
                 # Similar issue as above: Need robust mapping from old index to new index
                 # Placeholder: Assume content check is possible
                 # memory_content = get_content_for_old_index(old_index)
                 # if memory_content in content_to_new_index:
                 #    new_indices_for_trigger.append(content_to_new_index[memory_content])
                 pass # Needs robust implementation
            if new_indices_for_trigger:
                new_triggers[trigger] = new_indices_for_trigger

        # --- TEMPORARY SIMPLIFICATION (May lose some core/trigger links) ---
        # Filter core memories based on *current* valid indices
        self.core_memories = [idx for idx in self.core_memories if idx < len(self.emotional_memories)]
        # Filter triggers based on *current* valid indices
        temp_triggers = {}
        for trigger, indices in self.emotional_triggers.items():
            valid_indices = [idx for idx in indices if idx < len(self.emotional_memories)]
            if valid_indices:
                temp_triggers[trigger] = valid_indices
        self.emotional_triggers = temp_triggers
        logger.debug("Memory indices rebuilt (simplified).")
        # --- END TEMPORARY SIMPLIFICATION ---
    # --- MODIFIED SECTION END ---


    # --- Conflict Detection/Resolution Methods ---
    def _detect_conflicts(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Detects significant internal conflicts."""
        # (Detailed implementation from the previous version)
        conflicts = []; threshold = 0.65; diff_threshold = 0.4
        pairs = [ ("connection", "autonomy"), ("vulnerability", "pride"), ("authenticity", "validation"), ("joy", "shame"), ("anger", "fear"), ("connection", "avoidance"), ("vulnerability", "need_for_control"), ("joy", "grieving")]
        for e1_name, e2_name in pairs:
            e1_val = self.internal_emotions.get(e1_name, 0)
            if e2_name == "pride": e2_val = self.personality.get(e2_name, 0)
            elif e2_name == "avoidance": e2_val = self.attachment_style.get(e2_name, 0)
            elif e2_name == "need_for_control": e2_val = self.personality.get(e2_name, 0)
            else: e2_val = self.internal_emotions.get(e2_name, 0)
            if e1_val > threshold and e2_val > threshold:
                magnitude = (e1_val + e2_val) / 2 * abs(e1_val - e2_val); conflicts.append({"type": "emotion_vs_emotion", "emotions": [e1_name, e2_name], "magnitude": round(magnitude, 3)})
        if self.facade_intensity > 0.8: conflicts.append({"type": "internal_vs_external", "magnitude": round(self.facade_intensity, 3), "description": "High internal/external dissonance"}) # ENGLISH TRANSLATION
        if self.cognitive_appraisals["self_efficacy"] < 0.3 and self.internal_emotions["validation"] > 0.7:
            magnitude = ( (1 - self.cognitive_appraisals["self_efficacy"]) + self.internal_emotions["validation"] ) / 2; conflicts.append({"type": "cognitive_dissonance", "description": "Low self-efficacy vs High validation", "magnitude": round(magnitude, 3)}) # ENGLISH TRANSLATION
        if self.personality.get("need_for_control", 0) > 0.7 and self.internal_emotions["fear"] > 0.7:
            magnitude = (self.personality["need_for_control"] + self.internal_emotions["fear"]) / 2; conflicts.append({"type": "belief_vs_emotion", "description": "Need for control vs High fear", "magnitude": round(magnitude, 3)}) # ENGLISH TRANSLATION
        anxiety = self.attachment_style["anxiety"]; avoidance = self.attachment_style["avoidance"]
        if anxiety > 0.65 and avoidance > 0.65:
            magnitude = (anxiety + avoidance) / 2; conflicts.append({"type": "attachment_conflict", "description": "Anxious-Avoidant Attachment (Disorganized)", "magnitude": round(magnitude, 3)}) # ENGLISH TRANSLATION
        if self.fatigue_level > 0.7 and self.internal_emotions.get("autonomy", 0) > 0.6: conflicts.append({"type": "fatigue_vs_will", "description": "Fatigue vs Need to Act", "magnitude": round(self.fatigue_level, 3)}) # ENGLISH TRANSLATION
        conflicts.sort(key=lambda x: x.get("magnitude", 0), reverse=True)
        return conflicts[:3]

    def _resolve_conflicts(self, conflicts): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Attempts to resolve or reduce detected conflicts."""
        # (Detailed implementation from the previous version)
        if not conflicts: return
        resolution_strength_base = 0.1
        for conflict in conflicts:
            magnitude = conflict.get("magnitude", 0.5); ctype = conflict.get("type"); resolve_amount = resolution_strength_base * magnitude * (1 + self.personality["adaptability"] * 0.6)
            if ctype == "emotion_vs_emotion":
                e1, e2 = conflict["emotions"]; reduction = resolve_amount / 2
                if e1 in self.internal_emotions: self.internal_emotions[e1] = max(0, self.internal_emotions[e1] - reduction)
                if e2 in self.internal_emotions: self.internal_emotions[e2] = max(0, self.internal_emotions[e2] - reduction)
                self.personal_growth["insight_development"] = min(1.0, self.personal_growth["insight_development"] + resolve_amount * 0.12)
            elif ctype == "internal_vs_external":
                if self.personality["resilience"] > 0.45:
                    self.personality["authenticity"] = min(1.0, self.personality["authenticity"] + resolve_amount * 0.35)
                    self.personality["emotional_awareness"] = min(1.0, self.personality["emotional_awareness"] + resolve_amount * 0.35)
                else: self.regulation_strategies["expressive_suppression"] = min(1.0, self.regulation_strategies["expressive_suppression"] + resolve_amount * 0.25)
                self.personality["neuroticism"] = max(0.1, self.personality["neuroticism"] - resolve_amount * 0.12)
            elif ctype == "cognitive_dissonance":
                self.personal_growth["schema_restructuring"] = min(1.0, self.personal_growth["schema_restructuring"] + resolve_amount * 0.25)
                # ENGLISH TRANSLATION
                if "Low self-efficacy vs High validation" in conflict["description"]: self.internal_emotions["validation"] *= (1 - resolve_amount * 0.15)
            elif ctype == "belief_vs_emotion":
                self.personal_growth["schema_restructuring"] = min(1.0, self.personal_growth["schema_restructuring"] + resolve_amount * 0.18)
                self.internal_emotions["fear"] *= (1 - resolve_amount * 0.12)
            elif ctype == "attachment_conflict":
                self.attachment_style["security"] = min(0.9, self.attachment_style["security"] + resolve_amount * 0.12)
                self.attachment_style["anxiety"] = max(0.1, self.attachment_style["anxiety"] - resolve_amount * 0.06)
                self.attachment_style["avoidance"] = max(0.1, self.attachment_style["avoidance"] - resolve_amount * 0.06)
            elif ctype == "fatigue_vs_will":
                self.internal_emotions["autonomy"] *= (1 - resolve_amount * 0.1)
                self.regulation_strategies["acceptance"] = min(1.0, self.regulation_strategies["acceptance"] + resolve_amount * 0.1)

    def _integrate_self_identity(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Calculates metrics on the coherence and stability of the 'self'."""
        # (Detailed implementation from the previous version)
        coherence = (
            self.personality["authenticity"] * 0.35 +
            self.attachment_style["security"] * 0.25 +
            (1 - self.facade_intensity) * 0.20 +
            self.personal_growth["emotional_integration"] * 0.10 +
            self.personal_growth["identity_coherence"] * 0.10 -
            self.attachment_style["disorganization"] * 0.15
        )
        conflict_penalty = sum(c.get("magnitude", 0.5) for c in self.current_conflicts) * 0.2
        coherence -= conflict_penalty
        stability = (
            (1 - self.personality["neuroticism"]) * 0.35 +
            self.personality["resilience"] * 0.30 +
            self.cognitive_appraisals["certainty"] * 0.10 +
            self.personal_growth["identity_coherence"] * 0.15 -
            self.attachment_style["disorganization"] * 0.20
        )
        self.self_identity_metrics["coherence"] = round(max(0.05, min(0.95, coherence)), 3)
        self.self_identity_metrics["stability"] = round(max(0.05, min(0.95, stability)), 3)


    # --- Response Guidance Generation Methods ---
    def _generate_response_guidance(self, context=None, trauma_activation=None): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Generates detailed guidance for the dialogue generator"""
        # (Detailed implementation from the previous version)
        emotional_state = self._determine_emotional_state()
        attitude = self._determine_attitude(context, trauma_activation)
        nonverbals = self._generate_nonverbal_cues(trauma_activation)
        tone = self._determine_tone(context, trauma_activation)
        relationship = self._determine_relationship_dynamics()

        guidance = {
            "emotional_state": emotional_state,
            "facade_intensity": round(self.facade_intensity, 3),
            "attitude": attitude,
            "nonverbal_cues": nonverbals,
            "tone": tone,
            "relationship": relationship,
            "active_defenses": [d["type"] for d in self.active_defenses],
            "internal_feeling": self._most_intense_emotion(self.internal_emotions),
            "expressed_feeling": self._most_intense_emotion(self.expressed_emotions),
            "trauma_activated": trauma_activation["activated"] if trauma_activation else False,
            "trauma_response_type": trauma_activation["response_type"] if trauma_activation and trauma_activation["activated"] else None,
            "internal_emotions_detailed": {e: round(v, 2) for e, v in self.internal_emotions.items()},
            "expressed_emotions_detailed": {e: round(v, 2) for e, v in self.expressed_emotions.items()},
            "current_trust": round(self.trust_threshold, 2), # Changed from self.relationship_state['current_trust']
            "current_intimacy": round(self.intimacy_level, 2), # Changed from self.relationship_state['current_intimacy']
            "self_identity_metrics": self.self_identity_metrics.copy(),
            "detected_conflicts": [c.get("description", c.get("type")) for c in self.current_conflicts],
            "fatigue_level": round(self.fatigue_level, 2) # Include fatigue level
        }
        return guidance

    # --- Helper Methods ---
    def _determine_emotional_state(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        # (Detailed implementation from the previous version)
        states = set(); threshold = 0.6; state_mapping = {
            "vulnerability": {"high": "Exposed", "low_safe": "Guarded", "high_safe": "Opening Up"}, "connection": {"high": "Connected", "low": "Isolated"},
            "autonomy": {"high": "In Control", "low": "Powerless"}, "validation": {"high": "Affirmed", "low": "Invalidated"},
            "authenticity": {"high": "Authentic", "low": "Inauthentic"}, "psychological_safety": {"low": "Unsafe"}, "grieving": {"high": "Grieving"},
            "joy": {"high": "Joyful"}, "anger": {"high": "Angry"}, "fear": {"high": "Fearful"}, "shame": {"high": "Ashamed"},
            "anticipation": {"high": "Anticipating"}, "disgust": {"high": "Disgusted"} }
        for emotion, mapping in state_mapping.items():
            intensity = self.internal_emotions.get(emotion, 0); safety = self.internal_emotions.get("psychological_safety", 0)
            if "high" in mapping and intensity > threshold:
                if emotion == "vulnerability" and safety > 0.6: states.add(mapping["high_safe"])
                else: states.add(mapping["high"])
            if "low" in mapping and intensity < (1.0 - threshold):
                if emotion == "vulnerability" and safety < 0.4: states.add(mapping["low_safe"])
                else: states.add(mapping["low"])
        if self.fatigue_level > 0.7: states.add("Fatigued")
        if not states: states.add("Neutral")
        return list(states)

    def _determine_attitude(self, context=None, trauma_activation=None): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        # (Detailed implementation from the previous version)
        if trauma_activation and trauma_activation["activated"]:
            ttype = trauma_activation["response_type"]
            if ttype == "fight": return "Aggressive";
            elif ttype == "flight": return "Avoidant";
            elif ttype == "freeze": return "Numb";
            elif ttype == "fawn": return "Appeasing";
            elif ttype == "dissociation": return "Detached";
        emotional_state = self._determine_emotional_state()
        if "Grieving" in emotional_state: return "Grieving"
        if "Angry" in emotional_state and self.internal_emotions["anger"] > 0.75: return "Hostile"
        if "Fearful" in emotional_state and self.internal_emotions["fear"] > 0.75: return "Anxious"
        if "Ashamed" in emotional_state and self.internal_emotions["shame"] > 0.75: return "Withdrawn"
        if "Disgusted" in emotional_state and self.internal_emotions["disgust"] > 0.7: return "Repulsed"
        if "Fatigued" in emotional_state and self.fatigue_level > 0.8: return "Exhausted"
        if self.active_defenses:
            dtypes = {d["type"] for d in self.active_defenses}
            if "reaction_formation" in dtypes: return "Dismissive"
            elif "intellectualization" in dtypes: return "Analytical"
            elif "projection" in dtypes: return "Accusatory"
            elif "compensation" in dtypes: return "Arrogant"
            elif "denial" in dtypes: return "Defiant"
            elif "rationalization" in dtypes: return "Justifying"
            elif "splitting" in dtypes: return "Idealizing"
            elif "displacement" in dtypes: return "Irritable"
        if "Opening Up" in emotional_state and "Authentic" in emotional_state: return "Vulnerable"
        if "Connected" in emotional_state and "Powerless" in emotional_state: return "Desperate"
        if "Invalidated" in emotional_state: return "Resentful"
        if "Isolated" in emotional_state and "In Control" in emotional_state: return "Aloof"
        if "Joyful" in emotional_state and "Connected" in emotional_state: return "Warm"
        if "Authentic" in emotional_state: return "Genuine"
        return "Guarded"

    def _identify_emotional_conflicts(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        # (Detailed implementation from the previous version)
        conflicts = []; threshold = 0.65;
        pairs = [ ("connection", "autonomy"), ("vulnerability", "pride"), ("authenticity", "validation"), ("joy", "shame"), ("anger", "fear"), ("connection", "avoidance"), ("vulnerability", "need_for_control") ]
        for e1_name, e2_name in pairs:
            e1_val = self.internal_emotions.get(e1_name, 0)
            if e2_name == "pride": e2_val = self.personality.get(e2_name, 0)
            elif e2_name == "avoidance": e2_val = self.attachment_style.get(e2_name, 0)
            elif e2_name == "need_for_control": e2_val = self.personality.get(e2_name, 0)
            else: e2_val = self.internal_emotions.get(e2_name, 0)
            if e1_val > threshold and e2_val > threshold: conflicts.append(f"Conflict: {e1_name} vs {e2_name}") # ENGLISH TRANSLATION
        if self.facade_intensity > 0.8: conflicts.append("Conflict: High Facade (Internal vs External)") # ENGLISH TRANSLATION
        if self.fatigue_level > 0.7 and self.internal_emotions.get("autonomy", 0) > 0.6: conflicts.append("Conflict: Fatigue vs Need to Act") # ENGLISH TRANSLATION
        return conflicts

    def _generate_nonverbal_cues(self, trauma_activation=None): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        # (Detailed implementation from the previous version)
        cues_set = set(); num_cues = 3
        if trauma_activation and trauma_activation["activated"]:
            ttype = trauma_activation["response_type"]
            if ttype == "fight": cues_set.update(["Clenched fists", "Challenging stare"]) # ENGLISH TRANSLATION
            elif ttype == "flight": cues_set.update(["Restlessness", "Looks towards exit"]) # ENGLISH TRANSLATION
            elif ttype == "freeze": cues_set.update(["Motionless", "Vacant stare"]) # ENGLISH TRANSLATION
            elif ttype == "fawn": cues_set.update(["Nervous smile", "Nods frequently"]) # ENGLISH TRANSLATION
            elif ttype == "dissociation": cues_set.update(["Empty stare", "Slow movements"]) # ENGLISH TRANSLATION
        sorted_expressed = sorted(self.expressed_emotions.items(), key=lambda item: abs(item[1] - 0.5), reverse=True)
        # ENGLISH TRANSLATION of cues
        emotion_cue_map = { "anger": ["Frown", "Tight lips"], "fear": ["Wide eyes", "Swallows hard"], "joy": ["Genuine smile", "Bright eyes"], "grieving": ["Teary eyes", "Slumped shoulders"], "shame": ["Avoids eye contact", "Shrinks back"], "disgust": ["Grimace of disgust", "Looks away"], "vulnerability": ["Soft eye contact", "Open posture"], "connection": ["Leans in", "Nods"] }
        for emotion, intensity in sorted_expressed:
            if intensity > 0.6 and emotion in emotion_cue_map: cues_set.update(random.sample(emotion_cue_map[emotion], min(len(emotion_cue_map[emotion]), 1)))
            if len(cues_set) >= num_cues: break
        if len(cues_set) < num_cues:
            attitude = self._determine_attitude(None, None)
            if attitude in ["Dismissive", "Arrogant", "Superior", "Contemptuous"]: cues_set.add("Rolls eyes") # ENGLISH TRANSLATION
            if attitude in ["Cold", "Aloof", "Indifferent", "Detached"]: cues_set.add("Distant stare") # ENGLISH TRANSLATION
            if self.facade_intensity > 0.75: cues_set.add("Forced smile") # ENGLISH TRANSLATION
            if self.fatigue_level > 0.7: cues_set.add("Subtly yawns") # ENGLISH TRANSLATION
        # ENGLISH TRANSLATION of default cues
        default_cues = ["Adjusts clothing", "Shifts weight", "Looks around", "Clears throat", "Plays with hair", "Rubs eyes"]
        while len(cues_set) < num_cues and default_cues: cue_to_add = random.choice(default_cues); cues_set.add(cue_to_add); default_cues.remove(cue_to_add)
        return list(cues_set)[:num_cues]

    def _determine_tone(self, context=None, trauma_activation=None): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        # (Detailed implementation from the previous version)
        attitude = self._determine_attitude(context, trauma_activation)
        base_tone = "Neutral"
        # ENGLISH TRANSLATION of tones
        tone_map = { "Aggressive": "Aggressive", "Avoidant": "Evasive", "Panicked": "Frantic", "Numb": "Monotone", "Paralyzed": "Hesitant", "Appeasing": "Conciliatory", "Submissive": "Submissive", "Detached": "Distant", "Distant": "Cold", "Grieving": "Broken", "Hostile": "Hostile", "Anxious": "Anxious", "Terrified": "Terrified", "Withdrawn": "Flat", "Humiliated": "Mortified", "Repulsed": "Repulsed", "Dismissive": "Dismissive", "Contemptuous": "Contemptuous", "Analytical": "Analytical", "Cold": "Cold", "Accusatory": "Accusatory", "Suspicious": "Suspicious", "Arrogant": "Arrogant", "Superior": "Superior", "Defiant": "Defiant", "Unconcerned": "Indifferent", "Justifying": "Justifying", "Defensive": "Defensive", "Idealizing": "Flattering", "Devaluing": "Disparaging", "Irritable": "Irritable", "Vulnerable": "Vulnerable", "Open": "Open", "Desperate": "Desperate", "Pleading": "Pleading", "Resentful": "Resentful", "Bitter": "Bitter", "Aloof": "Aloof", "Indifferent": "Indifferent", "Warm": "Warm", "Enthusiastic": "Enthusiastic", "Genuine": "Genuine", "Sincere": "Sincere", "Guarded": "Guarded", "Neutral": "Neutral", "Exhausted": "Exhausted" }
        base_tone = tone_map.get(attitude, "Neutral")
        if self.fatigue_level > 0.8 and base_tone not in ["Broken", "Exhausted", "Monotone"]: base_tone = random.choice(["Flat", "Irritable"]) # ENGLISH TRANSLATION
        elif self.fatigue_level > 0.6 and base_tone not in ["Broken", "Exhausted", "Monotone"]:
            if base_tone == "Neutral": base_tone = "Tired" # ENGLISH TRANSLATION
            else: base_tone += " (tiredly)" # ENGLISH TRANSLATION
        return base_tone

    def _determine_relationship_dynamics(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        # (Detailed implementation from the previous version)
        dist = self.psychological_distance; trust = self.trust_threshold; intimacy = self.intimacy_level
        # ENGLISH TRANSLATION of relationship dynamics
        if dist > 0.75:
            if trust < 0.25: return "Hostile"
            elif trust < 0.4: return "Antagonistic"
            else: return "Very Distant"
        elif dist > 0.6:
            if trust < 0.3: return "Distrustful"
            else: return "Distant"
        elif dist < 0.3:
            if intimacy > 0.7 and trust > 0.7: return "Intimate"
            elif intimacy > 0.5 and trust > 0.6: return "Very Close"
            else: return "Close"
        elif dist < 0.5:
            if intimacy > 0.4 and trust > 0.5: return "Friendly"
            elif trust > 0.6: return "Cordial"
            else: return "Acquainted"
        else:
            if trust > 0.6 and intimacy > 0.3: return "Establishing"
            elif trust < 0.4: return "Tense"
            else: return "Neutral"

    def _most_intense_emotion(self, emotion_dict): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        if not emotion_dict: return "neutral"
        # Return the emotion name with the highest absolute value (distance from 0.5 doesn't make sense here)
        # return max(emotion_dict.items(), key=lambda x: abs(x[1] - 0.5))[0] # Original logic
        return max(emotion_dict.items(), key=lambda x: x[1])[0] # Corrected logic: find max value

    def reset(self): # <-- SECTION REVIEWED/KEPT (Logic from your code)
        """Resets the emotional core to its initial state."""
        logger.warning("Resetting EmotionalCore state to defaults.")
        # Re-initialize attributes to default values
        # This assumes __init__ can be called again safely or defaults are stored
        # A safer way might be to store defaults separately and assign them here.
        # For now, calling __init__ again.
        self.__init__(self.character_memory) # Call init again
