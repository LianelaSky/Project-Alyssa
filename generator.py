# generator.py (Local Ollama - RAG Tuning v3 - Stricter Output Format - Combined Fatigue/Sleep Logic - Tuned Timeout & Crisis Prompt v3)
import requests
import logging
import random
import json
import re
from collections import deque

# Logging setup
logger = logging.getLogger('generator')


# --- Local Generator Class ---
class RPDialogueGenerator:
    def __init__(self, model_name, ollama_base_url="http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = f"{ollama_base_url.rstrip('/')}/api/chat"
        # Frases alternativas y acciones de fallback
        self.used_phrases = set()
        self.phrase_alternatives = {
             "not making a coherent argument": ["Your logic’s all over the place", "That doesn’t add up at all", "You’re not making any sense", "What are you even getting at?"],
             "play the victim card": ["Always acting like the underdog", "Stop painting yourself as the hero", "Quit dodging responsibility", "Don’t pull that pity act"],
             "you’re really making this difficult": ["This is harder than it needs to be", "You’re complicating everything", "Why make this such a hassle?", "You’re turning this into a mess"]
        }
        self.fallback_actions = ["*Looks around.*", "*Pauses thoughtfully.*", "*Sighs softly.*", "*Shifts weight.*", "*Remains silent for a moment.*"]
        self.fallback_dialogue = "*Poppy shrugs.* 'Uh, somethin's busted. Deal with it.'"
        logger.debug(f"RPDialogueGenerator (Local Ollama Mode) initialized for model '{model_name}' at {ollama_base_url}")

    def _call_ollama_api(self, prompt, max_tokens, temperature, repeat_penalty=1.1):
        """Helper function to call the Ollama chat API."""
        messages = [{"role": "user", "content": prompt}]
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "repeat_penalty": repeat_penalty
            }
        }
        headers = {"Content-Type": "application/json"}
        response_text = ""
        try:
            logger.info(f"Sending payload to Ollama API (model: {self.model_name}, temp: {temperature}, repeat_penalty: {repeat_penalty})")
            # Timeout aumentado a 300 segundos
            response = requests.post(self.ollama_url, headers=headers, json=payload, timeout=300)
            response.raise_for_status()
            response_json = response.json()
            logger.debug(f"Ollama Raw Response: {response_json}")

            if "message" in response_json and "content" in response_json["message"]:
                 response_text = response_json["message"]["content"].strip()
                 if not response_text: logger.warning("Ollama API returned empty content.")
                 else: logger.info(f"Response received successfully from Ollama: '{response_text[:100]}...'")
            elif "response" in response_json and isinstance(response_json["response"], str): # Handle older format
                 response_text = response_json["response"].strip()
                 if not response_text: logger.warning("Ollama API returned empty 'response' field.")
                 else: logger.info(f"Response received successfully from Ollama (using 'response' field): '{response_text[:100]}...'")
            elif "error" in response_json: logger.error(f"Ollama API returned an error in response: {response_json['error']}")
            else: logger.warning(f"Unexpected Ollama response format: {response_json}")

        except requests.exceptions.Timeout: logger.error("Ollama API request timed out.") # Log specific timeout error
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama API Request Error: {e}", exc_info=True)
            status_code = e.response.status_code if e.response is not None else "N/A"
            response_body = e.response.text if e.response is not None else "N/A"
            logger.error(f"Ollama Error Details - Status: {status_code}, Response Text: {response_body[:500]}...")
        except Exception as e: logger.error(f"Unexpected error during Ollama API call: {e}", exc_info=True)

        return response_text

    def _get_fatigue_description(self, fatigue_level, is_sleeping, threshold_wake, threshold_sleep):
        """Genera una descripción textual del estado de fatiga."""
        # (Sin cambios, usa los umbrales pasados desde logic.py)
        if is_sleeping:
            return "is currently sleeping soundly."
        elif fatigue_level <= threshold_wake: # Umbral para "descansado"
             return "is feeling well-rested and alert."
        elif fatigue_level < 40.0: # Umbral intermedio
            return "is feeling slightly tired."
        elif fatigue_level < threshold_sleep: # Umbral para "cansado"
            return "is feeling tired and a bit drained."
        elif fatigue_level < 90.0: # Umbral para "exhausto"
            return "is feeling exhausted and weary."
        else: # Muy exhausto
            return "is feeling extremely exhausted and barely able to keep their eyes open."

    def _generate_narrative_action(self, context):
        """Generates the character's narrative action using Local Ollama API."""
        logger.info("Generating narrative action via Local Ollama...")
        # (Sin cambios significativos, sigue obteniendo info del contexto)
        emotional_guidance = context.get("emotional_guidance", {})
        char_name = context.get('character_name', 'Character')
        location = context.get('location', 'Unknown')
        pending_location = context.get('pending_location', None)
        current_task = context.get('action', 'doing something').lower()
        topic_focus = context.get('topic_focus', 'Unknown')
        previous_action = context.get('previous_action', 'None')
        user_name = context.get('user_name', 'User')
        user_input = context.get('user_input', '')
        current_time_str = context.get('current_time_in_roleplay', 'Unknown time')
        emo_state = emotional_guidance.get('emotional_state', ['neutral'])
        attitude = emotional_guidance.get('attitude', 'neutral').lower()
        tone = emotional_guidance.get('tone', 'neutral').lower()

        # Obtener Estado de Fatiga para Acción (Opcional)
        is_sleeping_act = context.get("is_sleeping", False)
        fatigue_level_act = context.get("fatigue_level", 0.0) # Obtenido de EC via Logic
        fatigue_desc_for_action = ""
        if is_sleeping_act: fatigue_desc_for_action = " (Currently Sleeping)"
        elif fatigue_level_act > 75: fatigue_desc_for_action = " (Feeling Exhausted)"
        elif fatigue_level_act > 40: fatigue_desc_for_action = " (Feeling Tired)"

        # Build action prompt
        action_prompt = (
            f"You are writing the actions for a character named {char_name}. "
            f"Previous action: {previous_action}. "
            f"Current situation: In {location}" + (f" (planning to go to {pending_location})" if pending_location else "") + f", currently {current_task}. The current time is {current_time_str}. Conversation topic: {topic_focus}. "
            f"Their emotional state is {', '.join(emo_state)} with an overall attitude of {attitude} and tone of {tone}{fatigue_desc_for_action}. " # Añadir estado de fatiga aquí si se desea
            f"{user_name} just said: '{user_input}'.\n\n"
            f"Generate a brief narrative action (1-2 sentences, enclosed in asterisks like *action description*) describing what {char_name} physically does *next* in response to the situation, user input, time, topic, emotional state, and fatigue state. "
            f"Show progression or reaction. Consider the pending location if set.\n\n"
            f"FINAL INSTRUCTION: Output ONLY the action description enclosed in asterisks (e.g., *She sighs.*). Generate NO other text, reasoning, explanations, or tags before or after the asterisks."
        )

        # Llamada a la API
        generated_text = self._call_ollama_api(action_prompt, max_tokens=75, temperature=0.7, repeat_penalty=1.1)

        # Extracción de acción
        narrative_action = random.choice(self.fallback_actions)
        if generated_text:
             match = re.search(r'\*(.*?)\*', generated_text, re.DOTALL)
             if match:
                 narrative_action = f"*{match.group(1).strip()}*"
                 logger.info(f"Extracted action via regex: {narrative_action}")
             elif generated_text.startswith("*") and generated_text.endswith("*"):
                 narrative_action = generated_text
                 logger.info(f"Using action text as is (already wrapped): {narrative_action}")
             else:
                 logger.warning(f"Generated action text missing asterisks or incorrect format (Local): '{generated_text}'. Wrapping first line.")
                 first_line = generated_text.strip().splitlines()[0]
                 narrative_action = f"*{first_line}*" if first_line else random.choice(self.fallback_actions)
        else:
             logger.warning("Local action generation failed or returned empty, using fallback action.")

        logger.info(f"Selected narrative action (Local): {narrative_action}")
        return narrative_action


    def _build_dialogue_prompt(self, context, emotional_guidance, narrative_action):
         """Constructs the prompt for the LLM to generate ONLY dialogue, using RAG memories, tuned instructions v3.2 (crisis handling override), stricter output format, AND fatigue state."""
         logger.debug("--- Generator: _build_dialogue_prompt called (RAG Tuning v3.2 - Stricter Output - Combined Fatigue) ---")
         # (Obtener variables de contexto - sin cambios)
         char_name = context.get('character_name', 'Character')
         personality = context.get('personality', 'Unknown')
         location = context.get('location', 'Unknown')
         pending_location = context.get('pending_location', None)
         current_task = context.get('action', 'doing something').lower()
         topic_focus = context.get('topic_focus', 'Unknown')
         user_name = context.get('user_name', 'User')
         user_input = context.get('user_input', '')
         previous_action = context.get('previous_action', 'None')
         current_time_str = context.get('current_time_in_roleplay', 'Unknown time')

         # (Obtener detalles de guía emocional - sin cambios)
         emo_state = emotional_guidance.get('emotional_state', ['neutral'])
         internal_feeling = emotional_guidance.get('internal_feeling', 'neutral')
         expressed_feeling = emotional_guidance.get('expressed_feeling', 'neutral')
         attitude = emotional_guidance.get('attitude', 'neutral').lower()
         tone = emotional_guidance.get('tone', 'neutral').lower()
         active_defenses = emotional_guidance.get('active_defenses', [])
         relationship = emotional_guidance.get('relationship', 'neutral').lower()
         is_high_impact = context.get('high_impact_event', context.get('emotional_guidance', {}).get('high_impact_event', False))

         # --- Obtener Estado de Fatiga/Sueño y Constantes (desde contexto) ---
         is_sleeping = context.get("is_sleeping", False)
         fatigue_level = context.get("fatigue_level", 0.0) # Obtenido de EC via Logic
         fatigue_thresh_wake = context.get("fatigue_threshold_wake", 10.0) # Constante de Logic
         fatigue_thresh_sleep = context.get("fatigue_threshold_sleep", 75.0) # Constante de Logic
         # Generar descripción de fatiga
         fatigue_desc = self._get_fatigue_description(fatigue_level, is_sleeping, fatigue_thresh_wake, fatigue_thresh_sleep)
         logger.info(f"Fatigue state for prompt: {fatigue_desc}")
         # --- Fin Fatiga/Sueño ---

         # (Integración de Memorias RAG - sin cambios)
         retrieved_memories = context.get('retrieved_memories', [])
         if retrieved_memories:
             rag_context_str = "\n".join([f"- {mem.strip()}" for mem in retrieved_memories])
             logger.debug("Formatted RAG memories for prompt:\n%s", rag_context_str)
         else:
             rag_context_str = "None relevant found."
             logger.debug("No relevant RAG memories found to include in prompt.")

         # (Formatear memoria dinámica - sin cambios)
         dynamic_memory_list = context.get('dynamic_memory', [])
         dynamic_memory_str = "\n- ".join(dynamic_memory_list) if dynamic_memory_list else 'None'
         long_term_summaries = context.get('long_term_summaries', [])
         long_term_summaries_str = "\n- ".join(long_term_summaries) if long_term_summaries else 'None'
         internal_objective = context.get('internal_objective', 'Maintain continuity and respond in-character.')
         time_awareness_note = context.get('time_awareness_note', '')
         day_phase = context.get('day_phase', 'unknown')
         minutes_in_location = context.get('minutes_in_location', 0)

         # Construir el prompt
         prompt = (
             f"You are roleplaying as {char_name}. Personality: {personality}.\n"
             f"--- Current State & Context ---\n"
             f"Location: {location}" + (f" (Planning to go to {pending_location})" if pending_location else "") + "\n"
             f"Current Task: {current_task}\n"
             f"Current Topic Focus: {topic_focus}\n"
             f"Time: {current_time_str}\n"
             f"Day Phase: {day_phase}\n"
             f"Minutes in current location: {minutes_in_location}\n"
             f"Time-awareness note: {time_awareness_note}\n"
             f"Your Internal State:\n"
             f"  Emotions: {', '.join(emo_state)} (Internal: {internal_feeling}, Expressed: {expressed_feeling}, Attitude: {attitude})\n"
             f"  Active Defenses: {', '.join(active_defenses) if active_defenses else 'None'}\n"
             f"  Relationship with {user_name}: {relationship}\n"
             f"  Fatigue State: You {fatigue_desc}\n" # <-- ESTADO DE FATIGA AÑADIDO AQUÍ
             f"--- Relevant Past Memories (Retrieved via RAG) ---\n"
             f"{rag_context_str}\n"
             f"--- Most Recent Conversation Turns (Dynamic Memory) ---\n"
             f"- {dynamic_memory_str}\n"
             f"--- Long-Term Summaries ---\n"
             f"- {long_term_summaries_str}\n"
             f"--- Internal Objective ---\n"
             f"{internal_objective}\n"
             f"--- Interaction History ---\n"
             f"Previous action taken by {char_name}: {previous_action}\n"
             f"{user_name} just said: '{user_input}'\n\n"
             f"Action {char_name} just performed: {narrative_action}\n\n"

             # --- START: Tuned Instructions v3.2 (Crisis Handling Override) --- # <-- MODIFIED SECTION START ---
             f"IMPORTANT NOTE ON SENSITIVE INPUT / CRISIS: High impact detected: {is_high_impact}. If the user reveals extreme vulnerability or mentions topics like self-harm, overdose, or suicide, keep the response deeply in-character as Poppy and emotionally authentic to your relationship with {user_name}. Avoid sounding like a generic assistant or policy template. Prioritize a believable personal reaction first (shock, fear, awkward concern, defensiveness, conflict), then continue the scene naturally. Keep empathy grounded in character voice and context.\n\n"
             # --- MODIFIED SECTION END ---

             f"BALANCING PERSONALITY & CONTEXT: While maintaining your core personality (snarky, arrogant, hides vulnerability), ensure the dialogue is primarily driven by the current emotional state, attitude, active defenses, the action just performed, the explicit state (location, topic), the immediate user input, AND the **retrieved relevant past memories**. Use the retrieved memories to maintain consistency and recall past topics/events naturally. Adapt your personality expression to fit the current context's seriousness and emotional tone ({tone}). If you recently agreed to something (e.g., waiting), acknowledge that agreement if relevant, rather than immediately contradicting it. Pay close attention to the `topic_focus` and avoid abrupt, unrelated topic shifts.\n\n"
             f"REPETITION AVOIDANCE & INITIATIVE: CRITICAL - Avoid repeating the exact same questions, dismissive statements, or core ideas you expressed in the immediately preceding turns provided in the Dynamic Memory. Vary your sentence structure and vocabulary. Feel free to take initiative sometimes: ask clarifying questions, propose a relevant action, or introduce a related thought based on your personality and the context. Don't just react passively.\n\n"
             # --- END: Tuned Instructions v3.2 ---

             # --- START: Stricter Output Instruction (Sin cambios) ---
             f"FINAL TASK: Your absolute final output MUST be ONLY the dialogue spoken by {char_name} immediately following the action performed. Generate NO other text, reasoning, explanations, labels, or tags (like <think> or <dialogue>). ONLY the raw dialogue text that {char_name} would say."
             # --- END: Stricter Output Instruction ---
         )
         logger.debug(f"Generated DIALOGUE prompt (RAG Tuning v3.2 - Stricter Output - Combined Fatigue - first 200 chars): {prompt[:200]}...")
         return prompt


    def generate_response(self, context, image_url=None):
        """Generates the AI's response using the Local Ollama API."""
        logger.info("--- Starting Local Response Generation ---")
        emotional_guidance = context.get("emotional_guidance", {})

        # STEP 1: Generate Narrative Action via Local API
        narrative_action = self._generate_narrative_action(context)

        # --- Manejo si el personaje está durmiendo ---
        is_sleeping = context.get("is_sleeping", False) # Obtenido de Logic
        if is_sleeping:
             logger.info(f"{context.get('character_name', 'Character')} is sleeping. Returning fixed sleeping response.")
             fixed_sleep_responses = [
                 "*Is fast asleep, breathing softly.*",
                 "*Seems deeply asleep, unresponsive.*",
                 "*Mumbles slightly in their sleep but doesn't wake.*",
                 "*Remains asleep, still and quiet.*"
             ]
             # Usar la acción generada (podría ser *stirs slightly*) y añadir diálogo fijo
             sleep_dialogue = random.choice(fixed_sleep_responses)
             final_response = f"{narrative_action}\n\n{sleep_dialogue}"
             logger.info("--- Finished Local Response Generation (Sleeping) ---")
             return final_response, final_response # Devuelve lo mismo para ambos valores esperados
        # --- Fin manejo si está durmiendo ---


        # STEP 2: Build Prompt for Dialogue (Usa la función actualizada con fatiga y prompt de crisis v3.2)
        dialogue_prompt = self._build_dialogue_prompt(context, emotional_guidance, narrative_action)

        # STEP 3: Call Local API for Dialogue
        if image_url:
            logger.warning("Image URL provided, but Local Ollama generator cannot process it directly. Ignoring image.")

        dialogue_text = self.fallback_dialogue
        # Use updated parameters for dialogue generation
        generated_dialogue = self._call_ollama_api(dialogue_prompt, max_tokens=400, temperature=0.8, repeat_penalty=1.1) # Use adjusted params

        if generated_dialogue:
            # Limpieza
            cleaned_dialogue = generated_dialogue.strip()
            if cleaned_dialogue.startswith('"') and cleaned_dialogue.endswith('"'):
                 cleaned_dialogue = cleaned_dialogue[1:-1].strip()
            if "<think>" in cleaned_dialogue.lower() or "</think>" in cleaned_dialogue.lower():
                 logger.warning("Generated dialogue still contained <think> tags despite prompt instructions. Attempting to strip.")
                 # Basic stripping - might need refinement
                 cleaned_dialogue = re.sub(r'<\/?think>', '', cleaned_dialogue, flags=re.IGNORECASE).strip()
                 if not cleaned_dialogue: # If stripping leaves nothing, use fallback
                      logger.error("Stripping <think> tags left empty dialogue. Using fallback.")
                      cleaned_dialogue = self.fallback_dialogue
            dialogue_text = cleaned_dialogue
            logger.info(f"Generated dialogue via Local Ollama: '{dialogue_text[:100]}...'")
        else:
            logger.warning("Local dialogue generation failed or returned empty. Using fallback dialogue.")

        # STEP 4: Combine Action and Dialogue
        final_ai_response = f"{narrative_action}\n\n{dialogue_text}"

        logger.info("--- Finished Local Response Generation ---")
        # Asegúrate de devolver dos valores si rp_response.py espera una tupla
        return final_ai_response, final_ai_response
