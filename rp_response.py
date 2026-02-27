# rp_response.py (Local Ollama - configurable runtime)
import argparse
import logging
import logging.handlers
import os
import sys
import time
from dataclasses import dataclass

import requests

from active_memory import ActiveMemoryFile
from character_memory import CharacterMemory, UserMemory
from dynamic_memory import DynamicMemory
from emotionalcore import EmotionalCore
from generator import RPDialogueGenerator
from logic import RPLogic


@dataclass
class AppConfig:
    model_name: str
    ollama_base_url: str
    user_name: str
    seed_initial_context: bool


DEFAULT_MODEL_NAME = "qwen3:8b"
DEFAULT_MODEL_NAME = "mistral-small3.1:24b"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_USER_NAME = "Lin"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Project Alyssa roleplay loop.")
    parser.add_argument("--model", default=os.getenv("ALYSSA_OLLAMA_MODEL", DEFAULT_MODEL_NAME))
    parser.add_argument("--ollama-url", default=os.getenv("ALYSSA_OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL))
    parser.add_argument("--user-name", default=os.getenv("ALYSSA_USER_NAME", DEFAULT_USER_NAME))
    parser.add_argument(
        "--skip-initial-context",
        action="store_true",
        help="Do not seed the default initial context event into memory on startup.",
    )
    return parser.parse_args()


def build_config(args: argparse.Namespace) -> AppConfig:
    return AppConfig(
        model_name=args.model,
        ollama_base_url=args.ollama_url,
        user_name=args.user_name,
        seed_initial_context=not args.skip_initial_context,
    )


def configure_logging() -> None:
    log_formatter_detailed = logging.Formatter("%(asctime)s - %(levelname)-8s - %(name)-15s - %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    main_log_path = os.path.abspath("debug.log")
    memory_log_path = os.path.abspath("memories_debug.log")

    has_main_handler = any(
        isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", "") == main_log_path
        for handler in root_logger.handlers
    )
    if not has_main_handler:
        main_log_handler = logging.FileHandler(main_log_path, mode="a", encoding="utf-8")
        main_log_handler.setFormatter(log_formatter_detailed)
        main_log_handler.setLevel(logging.INFO)
        root_logger.addHandler(main_log_handler)

    memory_logger = logging.getLogger("memory")
    has_memory_handler = any(
        isinstance(handler, logging.FileHandler) and getattr(handler, "baseFilename", "") == memory_log_path
        for handler in memory_logger.handlers
    )
    if not has_memory_handler:
        memory_log_handler = logging.FileHandler(memory_log_path, mode="a", encoding="utf-8")
        memory_log_handler.setFormatter(log_formatter_detailed)
        memory_log_handler.setLevel(logging.DEBUG)
        memory_logger.addHandler(memory_log_handler)
    memory_logger.propagate = False


main_script_logger = logging.getLogger("rp_response")


def main(config: AppConfig):
    main_script_logger.info("--- Starting main function (Local Ollama Mode) ---")
    main_script_logger.info("--- Using Model: %s ---", config.model_name)
    main_script_logger.info("--- Ollama URL: %s ---", config.ollama_base_url)

    dialogue_generator = None
    logic = None
    character = None
    user = None

    try:
        main_script_logger.info("Initializing components...")
        character = CharacterMemory()
        active = ActiveMemoryFile()
        user = UserMemory()
        user.user_name = config.user_name
        emotional_core = EmotionalCore(character_memory=character)
        dynamic = DynamicMemory()

        main_script_logger.info("Attempting to initialize generator with model: %s", config.model_name)
        try:
            ping_response = requests.get(config.ollama_base_url, timeout=5)
            ping_response.raise_for_status()
            main_script_logger.info("Ollama server responded at %s.", config.ollama_base_url)

            dialogue_generator = RPDialogueGenerator(
                model_name=config.model_name,
                ollama_base_url=config.ollama_base_url,
            )
        except requests.exceptions.Timeout:
            main_script_logger.error("Ollama server connection timed out at %s.", config.ollama_base_url)
            print(f"ERROR: Connection to Ollama timed out at {config.ollama_base_url}. Is it running and responsive?")
            sys.exit(1)
        except requests.exceptions.ConnectionError:
            main_script_logger.error("Ollama server not reachable at %s.", config.ollama_base_url)
            print(f"ERROR: Cannot connect to Ollama at {config.ollama_base_url}. Please start Ollama.")
            sys.exit(1)
        except requests.exceptions.RequestException as req_err:
            main_script_logger.error("Error checking Ollama connection: %s", req_err, exc_info=True)
            print(f"ERROR: Could not verify Ollama connection. Error: {req_err}")
            sys.exit(1)

        main_script_logger.info("Initializing RPLogic (includes VectorMemoryStore)...")
        logic = RPLogic(
            character_memory=character,
            active_memory=active,
            user_memory=user,
            emotional_core=emotional_core,
            dynamic_memory=dynamic,
        )
        main_script_logger.info("Components initialized successfully (state loaded if available).")

    except ImportError as ie:
        main_script_logger.critical("Missing dependency while initializing: %s", ie, exc_info=True)
        print(f"FATAL: Missing dependency: {ie}. Install requirements with `pip install -r requirements.txt`.")
        sys.exit(1)
    except Exception as e:
        main_script_logger.error("Unhandled error during component initialization: %s", e, exc_info=True)
        print(f"FATAL: Unhandled error during initialization. Check debug.log. Error: {e}")
        sys.exit(1)

    if config.seed_initial_context:
        try:
            main_script_logger.info("Injecting initial context event into memory...")
            if logic and logic.vector_memory:
                initial_context_event_text = (
                    "Background: Lin fell asleep at Poppy's house yesterday, missing project work. "
                    "They are now in Science Class. Poppy is irritated about the extra work."
                )
                initial_metadata = {
                    "timestamp": time.time(),
                    "roleplay_time": logic.current_roleplay_time.isoformat(),
                    "location": logic.dynamic_memory.location,
                    "action": logic.dynamic_memory.current_action,
                    "topic": logic.current_topic_focus,
                    "type": "system_context",
                }
                logic.vector_memory.add_memory(initial_context_event_text, metadata=initial_metadata)
                if logic.active_memory:
                    logic.dynamic_memory.add_memory(f"System Context: {initial_context_event_text}", logic.active_memory)
                else:
                    logic.dynamic_memory.add_memory(f"System Context: {initial_context_event_text}")
                main_script_logger.info("Initial context event added to VectorMemoryStore and DynamicMemory.")
            else:
                main_script_logger.warning("Skipping initial context injection: Logic or VectorMemoryStore not available.")
        except Exception as init_mem_err:
            main_script_logger.error("Error injecting initial context event: %s", init_mem_err, exc_info=True)

    current_location = logic.dynamic_memory.location if logic and logic.dynamic_memory else "Unknown Location"
    user_name_for_opening = user.user_name if user and hasattr(user, "user_name") else "User"

    opening_text = (
        f"*Poppy glances at {user_name_for_opening} across the cluttered desk in the {current_location}, "
        f"her perfectly manicured nails tapping impatiently.*\n"
        f"'Ugh, {user_name_for_opening}, I can't believe you fell asleep at my house yesterday,' "
        f"*she snaps, her voice dripping with irritation.*\n"
        "'Now we're stuck doing extra work because of you. You're lucky I'm even here to fix this mess. "
        "So, what's your excuse this time?'"
    )
    print(opening_text)
    print("\n" + "-" * 50 + "\n")

    main_script_logger.info("Entering main interactive loop...")
    while True:
        try:
            user_name_for_prompt = user.user_name if user else "User"
            user_input = input(f"{user_name_for_prompt} -> ")
        except (EOFError, KeyboardInterrupt):
            if logic:
                logic._save_state()
                print("\nInput interrupted. State saved (if possible). Ending roleplay.")
            else:
                print("\nInput interrupted before logic initialized. Cannot save state. Exiting.")
            break

        if user_input.lower() in ["quit", "exit"]:
            if logic:
                logic._save_state()
                print("State saved. Roleplay ended. Bye!")
            else:
                print("Exiting before logic initialized. Cannot save state. Bye!")
            break

        image_url = None
        user_text_for_context = user_input
        if user_input.lower() == "image":
            try:
                image_url = input("Enter the image URL: ")
                user_text_about_image = input("Enter your message about the image: ")
                user_text_for_context = user_text_about_image
            except (EOFError, KeyboardInterrupt):
                print("\nInput cancelled. Please try again.")
                continue

        try:
            if not logic or not dialogue_generator:
                print("ERROR: Core components not initialized. Exiting.")
                break

            context = logic.construct_context(user_text_for_context)
            ai_text_to_display, ai_text_for_memory = dialogue_generator.generate_response(context, image_url=image_url)

            if logic.active_memory:
                memory_input = user_input if not image_url else f"{user_text_about_image} [Image: {image_url}]"
                logic.manage_dynamic_memory(memory_input, ai_text_for_memory)
            else:
                main_script_logger.warning("Active memory missing when calling manage_dynamic_memory.")

            current_rp_time_obj = logic.current_roleplay_time
            time_str = current_rp_time_obj.strftime("%I:%M %p")
            char_name = character.character_name if character else "Character"
            print(f"\n[Time: {time_str}] - {char_name}: {ai_text_to_display}")
            print("\n" + "-" * 50 + "\n")

        except Exception as e:
            main_script_logger.error("Error during response generation cycle: %s", e, exc_info=True)
            fallback_dialogue = getattr(dialogue_generator, "fallback_dialogue", "*Something went wrong.*")
            char_name = character.character_name if character else "Character"
            print(f"\n{char_name}: {fallback_dialogue}")
            print(f"[Error occurred. Check debug.log. Error: {e}]")
            print("\n" + "-" * 50 + "\n")


if __name__ == "__main__":
    configure_logging()
    args = parse_args()
    config = build_config(args)
    main_script_logger.info("--- Script starting execution ---")
    main(config)
    main_script_logger.info("--- Script finished ---")
