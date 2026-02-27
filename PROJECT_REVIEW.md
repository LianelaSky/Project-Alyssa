# Project Alyssa – Technical Review

## What this code is for
This repository is built for a **stateful roleplay chatbot experience** centered on a character named Poppy.
It runs in a terminal, calls a local Ollama model for responses, and keeps continuity through multiple memory layers and saved state.

## How this works
- `rp_response.py` is the entry point and interactive loop.
- `logic.py` builds response context and tracks roleplay time, topic, location, and sleep/fatigue-related state.
- `generator.py` calls Ollama (`/api/chat`) and formats roleplay dialogue/action output.
- `vector_memory.py` uses FAISS + sentence-transformers for vector memory retrieval and persistence.
- `active_memory.py`, `dynamic_memory.py`, `character_memory.py`, and `emotionalcore.py` handle short-term memory, relationship traits, and emotional state.

## What is needed
1. Python 3.9+.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run Ollama locally and ensure the configured model exists.
4. Start the app:
   ```bash
   python rp_response.py
   ```

## Runtime configuration (new)
You can now avoid hardcoded runtime values and pass configuration via CLI/env:

- `--model` or `ALYSSA_OLLAMA_MODEL`
- `--ollama-url` or `ALYSSA_OLLAMA_BASE_URL`
- `--user-name` or `ALYSSA_USER_NAME`
- `--skip-initial-context` to skip injecting the default context seed

Examples:
```bash
python rp_response.py --model mistral --user-name Lia
ALYSSA_OLLAMA_BASE_URL=http://127.0.0.1:11434 python rp_response.py
```

## What is not strictly needed
- Existing `.log`, `.json`, and `.faiss` files are runtime artifacts and can be recreated.
- `start.txt` is optional convenience.

## Improvements made to weak points
- **Hardcoded settings reduced** by adding CLI + env-based configuration in `rp_response.py`.
- **Fragile logging setup improved** with guarded handler registration so repeated loads don't stack duplicate file handlers.
- **Startup flexibility improved** by allowing optional skip of initial context injection.

## How it looks (UX)
- Terminal-based interactive conversation.
- Starts with a narrative opener from Poppy.
- Prompt format: `<user_name> ->`.
- Supports:
  - regular text interaction,
  - `image` flow (URL + user description),
  - `exit`/`quit` to save and end.

## Validation notes
- `python -m py_compile *.py` passes.
- Runtime execution in this environment is still blocked by unavailable package index access for dependency install.

## Memory/thinking upgrades (new)
- Dynamic memory window increased from 3 to 8 events for better short-scene continuity.
- Long-term memory summaries are now persisted in `long_term_memory.json` (load/save), not only in RAM.
- Context now includes:
  - recent long-term summaries,
  - a lightweight internal objective derived from topic/crisis/scene state.
- Dialogue prompt now injects those long-term summaries and objective so responses stay more coherent and proactive.
