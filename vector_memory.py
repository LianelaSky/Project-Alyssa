# vector_memory.py
import logging
import time
import numpy as np
from sentence_transformers import SentenceTransformer # type: ignore
import faiss # type: ignore # Facebook AI Similarity Search
import os # Needed for checking file existence
import json # Needed for saving/loading data

# Get a logger specific to this module, inheriting from 'memory'
logger = logging.getLogger('memory.vector')

class VectorMemoryStore:
    def __init__(self, model_name='all-MiniLM-L6-v2', embedding_dim=None):
        """
        Initializes the vector memory store.

        Args:
            model_name (str): Name of the SentenceTransformer model to use.
            embedding_dim (int, optional): Dimension of the embeddings. If None, it's inferred.
        """
        logger.info("Initializing VectorMemoryStore...")
        self.model_name = model_name
        self.embedding_model = None
        self.index = None
        self.memory_data = []
        self.next_id = 0

        try:
            # Load the sentence transformer model
            self.embedding_model = SentenceTransformer(self.model_name)
            logger.info(f"Loaded SentenceTransformer model: {self.model_name}")

            # Get embedding dimension if not provided
            if embedding_dim is None:
                self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
                logger.info(f"Inferred embedding dimension: {self.embedding_dim}")
            else:
                self.embedding_dim = embedding_dim
                logger.info(f"Using provided embedding dimension: {self.embedding_dim}")

            # Initialize FAISS index
            # Using IndexIDMap to map FAISS internal IDs back to our sequential IDs
            self.index = faiss.IndexIDMap(faiss.IndexFlatL2(self.embedding_dim))
            logger.info(f"Initialized FAISS IndexIDMap with IndexFlatL2 (dim={self.embedding_dim})")

        except Exception as e:
            logger.critical(f"Failed to initialize SentenceTransformer model or FAISS index: {e}", exc_info=True)
            # Set flags or raise exception to indicate failure
            self.embedding_model = None
            self.index = None
            raise # Re-raise the exception to prevent using a non-functional store

        logger.info("VectorMemoryStore initialized successfully.")

    def add_memory(self, event_text, metadata=None):
        """
        Adds a new memory event to the store.

        Args:
            event_text (str): The text content of the memory event.
            metadata (dict, optional): Additional data associated with the memory
                                       (e.g., timestamp, emotions, location). Defaults to None.
        """
        # Check if initialization was successful
        if not self.embedding_model or not self.index:
             logger.error("Cannot add memory: VectorMemoryStore not initialized properly.")
             return

        if not isinstance(event_text, str) or not event_text.strip():
            logger.warning("Attempted to add empty or invalid memory text.")
            return

        logger.debug("--- VectorMemory: add_memory called ---")
        logger.debug("Input text: '%s...'", event_text[:100])
        logger.debug("Metadata: %s", metadata)

        try:
            # 1. Generate embedding
            embedding = self.embedding_model.encode([event_text], convert_to_numpy=True)
            if embedding.ndim == 1: embedding = np.expand_dims(embedding, axis=0)
            embedding = embedding.astype('float32')
            logger.debug(f"Generated embedding shape: {embedding.shape}")

            # 2. Prepare memory object
            memory_id = self.next_id
            memory_object = {
                "id": memory_id,
                "text": event_text,
                # Store embedding as list for JSON compatibility if needed, but FAISS uses numpy
                # "embedding": embedding.flatten().tolist(),
                "metadata": metadata if metadata else {}
            }
            if "timestamp" not in memory_object["metadata"]:
                 memory_object["metadata"]["timestamp"] = time.time()

            # 3. Store the memory object data (text + metadata)
            self.memory_data.append(memory_object)

            # 4. Add the embedding vector to the FAISS index with its ID
            faiss_id = np.array([memory_id], dtype='int64')
            self.index.add_with_ids(embedding, faiss_id)

            logger.info(f"Added memory ID {memory_id} to store and FAISS index. Index size: {self.index.ntotal}")
            self.next_id += 1

        except Exception as e:
            logger.error(f"Failed to add memory: {e}", exc_info=True)
            # Consider rolling back the addition to self.memory_data if index add fails
            if len(self.memory_data) == self.next_id + 1:
                 self.memory_data.pop()
                 logger.warning("Rolled back addition to memory_data due to error.")


        logger.debug("--- VectorMemory: add_memory finished ---")


    def retrieve_relevant_memories(self, query_text, k=5, threshold=None):
        """
        Retrieves the k most relevant memories based on semantic similarity.

        Args:
            query_text (str): The text to search for relevant memories.
            k (int): The maximum number of memories to retrieve.
            threshold (float, optional): A similarity threshold (e.g., L2 distance).
                                        Memories less similar than this are excluded.

        Returns:
            list[dict]: A list of the most relevant memory objects, ordered by similarity.
                        Returns empty list if no relevant memories are found or on error.
        """
        # Check if initialization was successful and index has items
        if not self.embedding_model or not self.index or self.index.ntotal == 0:
             logger.debug("Retrieval attempted but store not ready or index is empty.")
             return []
        if not isinstance(query_text, str) or not query_text.strip():
            logger.warning("Attempted retrieval with empty or invalid query text.")
            return []

        logger.debug("--- VectorMemory: retrieve_relevant_memories called ---")
        logger.debug("Query text: '%s...'", query_text[:100])
        logger.debug("k: %d, threshold: %s", k, threshold)

        retrieved_memories = []
        try:
            # 1. Generate query embedding
            query_embedding = self.embedding_model.encode([query_text], convert_to_numpy=True)
            if query_embedding.ndim == 1: query_embedding = np.expand_dims(query_embedding, axis=0)
            query_embedding = query_embedding.astype('float32')
            logger.debug(f"Query embedding shape: {query_embedding.shape}")

            # 2. Search the FAISS index
            # Ensure k is not greater than the number of items in the index
            actual_k = min(k, self.index.ntotal)
            if actual_k == 0: return [] # Should be caught by ntotal check above, but belt-and-suspenders
            logger.debug(f"Searching FAISS index with k={actual_k}")
            distances, ids = self.index.search(query_embedding, actual_k)
            logger.debug(f"FAISS search results - Distances: {distances}, IDs: {ids}")

            # Process results
            if ids.size > 0:
                result_ids = ids[0]
                result_distances = distances[0]

                for i, memory_id in enumerate(result_ids):
                    if memory_id == -1: continue # Skip invalid IDs

                    # Check distance threshold
                    distance = result_distances[i]
                    if threshold is not None and distance > threshold:
                        logger.debug(f"Memory ID {memory_id} skipped due to distance {distance} > threshold {threshold}")
                        continue

                    # Retrieve the full memory object
                    if 0 <= memory_id < len(self.memory_data):
                        # Important: Create a copy to avoid modifying the stored object
                        memory_object = self.memory_data[memory_id].copy()
                        # Add similarity score (L2 distance, smaller is better)
                        memory_object["similarity_score"] = float(distance)
                        retrieved_memories.append(memory_object)
                        logger.debug(f"Retrieved relevant memory ID {memory_id} with distance {distance}")
                    else:
                        logger.warning(f"FAISS returned ID {memory_id} which is out of bounds for memory_data (size {len(self.memory_data)}).")

            # Sort by similarity score (ascending for L2 distance)
            retrieved_memories.sort(key=lambda x: x.get("similarity_score", float('inf')))

        except Exception as e:
            logger.error(f"Failed to retrieve memories: {e}", exc_info=True)
            return []

        logger.info(f"Retrieved {len(retrieved_memories)} relevant memories for query.")
        logger.debug("--- VectorMemory: retrieve_relevant_memories finished ---")
        return retrieved_memories

    def save_memory(self, index_path="memory_index.faiss", data_path="memory_data.json"):
         """Saves the FAISS index and memory data to disk."""
         if not self.index:
              logger.error("Cannot save memory: FAISS index not initialized.")
              return
         logger.info(f"Saving FAISS index to {index_path} and data to {data_path}...")
         try:
             logger.debug(f"Writing FAISS index with {self.index.ntotal} vectors.")
             faiss.write_index(self.index, index_path)

             # Save memory_data (list of dicts) and next_id as JSON
             # Exclude the large embedding list from the JSON data file for efficiency
             data_to_save = [
                 {k: v for k, v in mem.items() if k != 'embedding'}
                 for mem in self.memory_data
             ]
             with open(data_path, 'w', encoding='utf-8') as f:
                 json.dump({"memory_data": data_to_save, "next_id": self.next_id}, f, ensure_ascii=False, indent=2)
             logger.info("Memory saved successfully.")
         except Exception as e:
             logger.error(f"Failed to save memory: {e}", exc_info=True)

    def load_memory(self, index_path="memory_index.faiss", data_path="memory_data.json"):
         """Loads the FAISS index and memory data from disk."""
         logger.info(f"Attempting to load FAISS index from {index_path} and data from {data_path}...")
         if os.path.exists(index_path) and os.path.exists(data_path):
             try:
                 # Load FAISS index
                 self.index = faiss.read_index(index_path)
                 # Ensure it's the expected type (IndexIDMap) after loading if needed
                 if not isinstance(self.index, faiss.IndexIDMap):
                      logger.warning(f"Loaded index from {index_path} is not IndexIDMap. Re-wrapping.")
                      # This might be necessary depending on how write_index/read_index handles IndexIDMap
                      # If it saves only the underlying index, we need to recreate the map
                      # This part might need adjustment based on faiss save/load behavior for IndexIDMap
                      base_index = self.index
                      self.index = faiss.IndexIDMap(base_index)
                      # We would need to re-add vectors with IDs from loaded data - complex!
                      # SAFER APPROACH: Assume write_index saves the map correctly. If issues arise, revisit.

                 logger.info(f"Loaded FAISS index. Size: {self.index.ntotal}")

                 # Load corresponding data
                 with open(data_path, 'r', encoding='utf-8') as f:
                     loaded_data = json.load(f)
                     self.memory_data = loaded_data.get("memory_data", [])
                     self.next_id = loaded_data.get("next_id", 0)
                 logger.info(f"Loaded memory data ({len(self.memory_data)} items). Next ID: {self.next_id}")

                 # Basic Consistency Check
                 if self.index.ntotal != len(self.memory_data):
                      logger.critical(f"CRITICAL INCONSISTENCY: Index size ({self.index.ntotal}) does not match loaded data size ({len(self.memory_data)}). Resetting memory.")
                      # Reset to empty state to avoid errors
                      self.__init__(model_name=self.model_name, embedding_dim=self.embedding_dim) # Re-initialize
                 else:
                      logger.info("Index and data sizes match.")

             except Exception as e:
                 logger.error(f"Failed to load memory: {e}", exc_info=True)
                 # Reset to empty state if loading fails
                 self.__init__(model_name=self.model_name, embedding_dim=self.embedding_dim) # Re-initialize
         else:
             logger.warning(f"Memory files not found ({index_path} or {data_path}). Starting with empty memory.")

