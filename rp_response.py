# rp_response.py (Local Ollama - Using Mistral - Added Time Prefix)
import logging
import logging.handlers
import sys
import time
import datetime
import json
import os
import requests # Needed to check Ollama server

# Import logic and component classes
from logic import RPLogic
from active_memory import ActiveMemoryFile # Assuming still needed for DynamicMemory init
from character_memory import CharacterMemory, UserMemory
# Import EmotionalCore if it's in its own file, otherwise ensure it's defined/imported correctly
try:
    from emotionalcore import EmotionalCore
except ImportError:
    # Handle case where EmotionalCore might be defined elsewhere or handle error
    logging.critical("Failed to import EmotionalCore. Ensure emotionalcore.py exists or class is defined.")
    # Define a placeholder or exit if critical
    class EmotionalCore: # Placeholder if import fails
        def __init__(self, *args, **kwargs): pass
        def process_interaction(self, *args, **kwargs): return {} # Return empty dict
        # Add other methods as needed or raise error
    # Or: sys.exit("EmotionalCore class not found.")

from dynamic_memory import DynamicMemory
# Import the local generator class
from generator import RPDialogueGenerator # Assuming generator file is named generator.py


# --- Advanced Logging Setup ---
# (Logging setup remains the same)
log_formatter_detailed = logging.Formatter('%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s')
log_formatter_simple = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s')
main_log_handler = logging.FileHandler("debug.log", mode='a', encoding='utf-8')
main_log_handler.setFormatter(log_formatter_detailed)
main_log_handler.setLevel(logging.INFO)
memory_log_handler = logging.FileHandler("memories_debug.log", mode='a', encoding='utf-8')
memory_log_handler.setFormatter(log_formatter_detailed)
memory_log_handler.setLevel(logging.DEBUG)
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
memory_logger = logging.getLogger('memory')
logic_logger = logging.getLogger('logic')
generator_logger = logging.getLogger('generator')
emotional_core_logger = logging.getLogger('emotional_core') # Changed from 'emotionalcore' to match typical naming
main_script_logger = logging.getLogger('rp_response')
root_logger.addHandler(main_log_handler)
memory_logger.addHandler(memory_log_handler)
memory_logger.propagate = False
# --- End Advanced Logging Setup ---

# --- Configuration ---
LOCAL_OLLAMA_MODEL_NAME = "mistral-small3.1:24b" # Using the Mistral model specified by user
LOCAL_OLLAMA_BASE_URL = "http://localhost:11434" # Default Ollama URL

def main():
    main_script_logger.info("--- Starting main function (Local Ollama Mode) ---")
    main_script_logger.info(f"--- Using Model: {LOCAL_OLLAMA_MODEL_NAME} ---") # Log the model being used

    # --- Initialization ---
    dialogue_generator = None
    logic = None # Initialize to None
    character = None # Initialize character to None
    user = None # Initialize user to None
    try:
        main_script_logger.info("Initializing components...")
        character = CharacterMemory() # Initialize here to access character_name later
        active = ActiveMemoryFile()
        user = UserMemory()
        user.user_name = "Lin" # Set user name
        # Instantiate EmotionalCore safely
        # Pass character memory if needed by EmotionalCore's __init__
        emotional_core = EmotionalCore(character_memory=character)
        dynamic = DynamicMemory()

        # --- Instantiate Local Generator ---
        main_script_logger.info(f"Attempting to use LocalGenerator with model: {LOCAL_OLLAMA_MODEL_NAME}")
        try:
             # Check Ollama server reachability
             ping_response = requests.get(LOCAL_OLLAMA_BASE_URL, timeout=5)
             ping_response.raise_for_status()
             main_script_logger.info(f"Ollama server responded at {LOCAL_OLLAMA_BASE_URL}.")

             # Instantiate the local generator
             dialogue_generator = RPDialogueGenerator(
                 model_name=LOCAL_OLLAMA_MODEL_NAME,
                 ollama_base_url=LOCAL_OLLAMA_BASE_URL
             )

        except requests.exceptions.Timeout:
             main_script_logger.error(f"Ollama server connection timed out at {LOCAL_OLLAMA_BASE_URL}.")
             print(f"ERROR: Connection to Ollama timed out at {LOCAL_OLLAMA_BASE_URL}. Is it running and responsive?")
             sys.exit(1)
        except requests.exceptions.ConnectionError:
             main_script_logger.error(f"Ollama server not reachable at {LOCAL_OLLAMA_BASE_URL}. Please ensure Ollama is running.")
             print(f"ERROR: Cannot connect to Ollama at {LOCAL_OLLAMA_BASE_URL}. Please start Ollama.")
             sys.exit(1)
        except requests.exceptions.RequestException as req_err:
             main_script_logger.error(f"Error checking Ollama connection: {req_err}", exc_info=True)
             print(f"ERROR: Could not verify Ollama connection. Error: {req_err}")
             sys.exit(1)
        except Exception as gen_init_err:
             main_script_logger.error(f"Error initializing RPDialogueGenerator: {gen_init_err}", exc_info=True)
             print(f"ERROR: Failed to initialize dialogue generator. Error: {gen_init_err}")
             sys.exit(1)


        # Initialize Logic (ensure vector_memory.py exists and dependencies are installed)
        main_script_logger.info("Initializing RPLogic (includes VectorMemoryStore)...")
        try:
            logic = RPLogic(
                character_memory=character,
                active_memory=active, # Pass active memory object
                user_memory=user,
                emotional_core=emotional_core,
                dynamic_memory=dynamic
            )
        except NameError as ne: # Catch if VectorMemoryStore wasn't imported
             main_script_logger.critical(f"Failed to initialize RPLogic, likely VectorMemoryStore missing: {ne}", exc_info=True)
             print(f"ERROR: Failed to initialize logic. Is vector_memory.py present and correct? Error: {ne}")
             sys.exit(1)
        except ImportError as ie: # Catch dependency import errors within VectorMemoryStore
             main_script_logger.critical(f"Failed to initialize RPLogic, likely missing RAG dependencies (sentence-transformers, faiss-cpu): {ie}", exc_info=True)
             print(f"ERROR: Failed to initialize logic due to missing dependencies. Did you run 'pip install sentence-transformers faiss-cpu'? Error: {ie}")
             sys.exit(1)
        except Exception as logic_init_err:
             main_script_logger.error(f"Error during RPLogic initialization: {logic_init_err}", exc_info=True)
             print(f"FATAL: Error during logic initialization. Check debug.log. Error: {logic_init_err}")
             sys.exit(1)

        main_script_logger.info("Components initialized successfully (state loaded if available).")

    except Exception as e: # General catch-all for initialization phase
        main_script_logger.error(f"Unhandled error during component initialization phase: {e}", exc_info=True)
        print(f"FATAL: Unhandled error during initialization. Check debug.log. Error: {e}")
        sys.exit(1)

    # --- Initial Setup & Context Injection ---
    try:
        main_script_logger.info("Injecting initial context event into memory...")
        if logic and logic.vector_memory:
             initial_context_event_text = "Background: Lin fell asleep at Poppy's house yesterday, missing project work. They are now in Science Class. Poppy is irritated about the extra work."
             initial_metadata = {
                 "timestamp": time.time(),
                 "roleplay_time": logic.current_roleplay_time.isoformat(),
                 "location": logic.dynamic_memory.location,
                 "action": logic.dynamic_memory.current_action,
                 "topic": logic.current_topic_focus,
                 "type": "system_context"
             }
             logic.vector_memory.add_memory(initial_context_event_text, metadata=initial_metadata)
             # Ensure active_memory is passed if required by add_memory
             if logic.active_memory:
                 logic.dynamic_memory.add_memory(f"System Context: {initial_context_event_text}", logic.active_memory)
             else:
                 logic.dynamic_memory.add_memory(f"System Context: {initial_context_event_text}") # Or handle error
             main_script_logger.info("Initial context event added to VectorMemoryStore and DynamicMemory.")
        else:
             main_script_logger.warning("Skipping initial context injection: Logic or VectorMemoryStore not available.")
    except Exception as init_mem_err:
         main_script_logger.error(f"Error injecting initial context event: {init_mem_err}", exc_info=True)


    # --- Roleplay Start ---
    # Ensure logic and user objects exist before accessing attributes
    current_location = "Unknown Location"
    user_name_for_opening = "User"
    if logic and logic.dynamic_memory:
        current_location = logic.dynamic_memory.location
    if user and hasattr(user, 'user_name'):
        user_name_for_opening = user.user_name

    opening_text = (
        f"*Poppy glances at {user_name_for_opening} across the cluttered desk in the {current_location}, "
        f"her perfectly manicured nails tapping impatiently.*\n"
        f"'Ugh, {user_name_for_opening}, I can't believe you fell asleep at my house yesterday,' "
        f"*she snaps, her voice dripping with irritation.*\n"
        f"'Now we're stuck doing extra work because of you. You're lucky I'm even here to fix this mess. "
        f"So, what's your excuse this time?'"
    )
    try:
        print(opening_text)
        print("\n" + "-"*50 + "\n")
        main_script_logger.info("Printed opening text and separator.")
    except Exception as e:
        main_script_logger.error(f"Error printing opening text/separator: {e}", exc_info=True)
        print("[Error displaying opening text - check console encoding? Continuing anyway...]")


    main_script_logger.info("Entering main interactive loop...")
    # --- Interactive Loop ---
    while True:
        try:
            # Ensure user object exists before accessing user_name
            user_name_for_prompt = user.user_name if user else "User"
            prompt_message = f"{user_name_for_prompt} -> "
            user_input = input(prompt_message)
            main_script_logger.debug(f"User input received: {user_input[:100]}...")
        except (EOFError, KeyboardInterrupt) as interrupt_err:
             main_script_logger.warning(f"Input interruption received ({type(interrupt_err).__name__}), attempting to save state before exiting.")
             if logic:
                 logic._save_state()
                 print("\nInput interrupted. State saved (if possible). Ending roleplay.")
             else:
                 print("\nInput interrupted before logic initialized. Cannot save state. Exiting.")
             break

        if user_input.lower() in ["quit", "exit"]:
            main_script_logger.info("Quit command received. Saving state...")
            if logic:
                try:
                    logic._save_state()
                    print("State saved. Roleplay ended. Bye!")
                except Exception as save_err:
                     main_script_logger.error(f"Error during final save state: {save_err}", exc_info=True)
                     print(f"\nError during final save state: {save_err}. Roleplay ended.")
            else:
                main_script_logger.warning("Quit command received but logic not initialized. Cannot save.")
                print("Exiting before logic initialized. Cannot save state. Bye!")
            break

        image_url = None
        user_text_for_context = user_input

        if user_input.lower() == "image":
            try:
                main_script_logger.info("Handling image input.")
                image_url = input("Enter the image URL: ")
                user_text_about_image = input("Enter your message about the image: ")
                user_text_for_context = user_text_about_image
            except (EOFError, KeyboardInterrupt):
                 main_script_logger.warning("Input cancelled during image prompt.")
                 print("\nInput cancelled. Please try again.")
                 continue

        # --- Generate Response ---
        try:
            main_script_logger.info("Constructing context...")
            if not logic or not dialogue_generator:
                 main_script_logger.error("Logic or Dialogue Generator not initialized. Cannot proceed.")
                 print("ERROR: Core components not initialized. Exiting.")
                 break

            context = logic.construct_context(user_text_for_context)
            main_script_logger.info("Context constructed.")

            main_script_logger.info(f"Generating response using Local generator ({LOCAL_OLLAMA_MODEL_NAME})...")
            ai_text_to_display, ai_text_for_memory = dialogue_generator.generate_response(context, image_url=image_url)
            main_script_logger.info("Response generated.")

            main_script_logger.info("Managing memory...")
            # Ensure active_memory is passed if needed by manage_dynamic_memory
            if logic.active_memory:
                 logic.manage_dynamic_memory(user_input if not image_url else f"{user_text_about_image} [Image: {image_url}]", ai_text_for_memory)
            else:
                 # Decide how to handle if active_memory is missing
                 # Maybe log a warning and proceed, or raise an error if critical
                 main_script_logger.warning("Active memory missing when calling manage_dynamic_memory.")
                 # logic.manage_dynamic_memory(...) # Call without active_memory if possible
            main_script_logger.info("Memory managed.")

            main_script_logger.info("Printing AI response...")
            try:
                # --- MODIFIED SECTION START: Add Time Prefix ---
                # Get current roleplay time from logic object
                current_rp_time_obj = logic.current_roleplay_time
                # Format the time as HH:MM AM/PM
                time_str = current_rp_time_obj.strftime("%I:%M %p")
                # Ensure character object exists before accessing character_name
                char_name = character.character_name if character else "Character"
                # Print the response with the time prefix
                print(f"\n[Time: {time_str}] - {char_name}: {ai_text_to_display}")
                # --- MODIFIED SECTION END ---
                print("\n" + "-"*50 + "\n")
                main_script_logger.info("AI response printed.")
            except Exception as e:
                 main_script_logger.error(f"Error printing AI response: {e}", exc_info=True)
                 char_name = character.character_name if character else "Character"
                 print(f"\n[{char_name} responded, but there was an error displaying it.]")
                 print("\n" + "-"*50 + "\n")

        except Exception as e:
            main_script_logger.error(f"An error occurred during response generation cycle: {e}", exc_info=True)
            fallback_dialogue = getattr(dialogue_generator, 'fallback_dialogue', "*Something went wrong.*")
            char_name = character.character_name if character else "Character"
            print(f"\n{char_name}: {fallback_dialogue}")
            print(f"[Error occurred. Check debug.log. Error: {e}]")
            print("\n" + "-"*50 + "\n")

    main_script_logger.info("--- Exiting main function ---")

if __name__ == "__main__":
    # Ensure logging is configured before the first log message
    # (Move logging setup here if not already done globally or handle potential errors)
    try:
        # Setup logging here if needed, or ensure it's done before this point
        pass
    except Exception as log_setup_err:
        print(f"FATAL: Error setting up logging: {log_setup_err}")
        sys.exit(1)

    main_script_logger.info("--- Script starting execution ---")
    main()
    main_script_logger.info("--- Script finished ---")
