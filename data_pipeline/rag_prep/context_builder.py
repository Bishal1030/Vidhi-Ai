import os
import sys
import logging
from typing import List, Dict, Any, Optional

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data_pipeline.indexing.embedder import LegalEmbedder
from data_pipeline.indexing.vector_store import LegalVectorStore

logger = logging.getLogger("context_builder")

class LegalContextBuilder:
    """
    Retrieves relevant legal chunks and constructs structured, citation-dense 
    context blocks to be fed into LLM prompts.
    """
    def __init__(self, collection_name: str = "vidhi_legal_acts", use_openai: bool = False):
        self.collection_name = collection_name
        self.embedder = LegalEmbedder(use_openai=use_openai)
        self.vector_store = LegalVectorStore()

    def retrieve_relevant_chunks(
        self, 
        query: str, 
        limit: int = 5, 
        filter_meta: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top matching chunks from Qdrant. 
        Guarantees coverage across multiple acts by querying each indexed act individually 
        to ensure smaller specialized acts (like the Citizenship Act) are not starved by 
        extremely large documents (like the Constitution).
        """
        import json
        logger.info(f"Retrieving top {limit} relevant chunks for query: '{query}'...")
        query_vector = self.embedder.embed_query(query)
        if not query_vector:
            logger.error("Failed to generate embedding vector for the search query.")
            return []

        # If a specific filter is already passed, run single search
        if filter_meta:
            return self.vector_store.search_collection(
                collection_name=self.collection_name,
                query_vector=query_vector,
                filter_meta=filter_meta,
                limit=limit
            )

        # Dynamically discover all act titles from structured json directories
        act_titles = []
        try:
            from data_pipeline.ingestion.config import STRUCTURED_ACTS_DIR
            if os.path.exists(STRUCTURED_ACTS_DIR):
                for file_name in os.listdir(STRUCTURED_ACTS_DIR):
                    if file_name.endswith(".json"):
                        with open(os.path.join(STRUCTURED_ACTS_DIR, file_name), "r", encoding="utf-8") as file:
                            data = json.load(file)
                            title = data.get("nepali_title") or data.get("title")
                            if title and title not in act_titles:
                                act_titles.append(title)
        except Exception as e:
            logger.warning(f"Failed to dynamically load act titles from config: {e}. Falling back to default search.")

        # Run vector search for each act to guarantee balanced context retrieval
        all_hits = []
        if act_titles:
            logger.info(f"Dynamically discovered acts for retrieval: {act_titles}")
            
            # Determine limit per act, giving a proportional slice to each act to ensure representation
            limit_per_act = max(4, limit // len(act_titles))
            logger.info(f"Retrieval quota per act: {limit_per_act} chunks")
            
            for title in act_titles:
                logger.info(f"Querying Qdrant for act: '{title}'...")
                # Search using the nepali_title filter
                hits = self.vector_store.search_collection(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    filter_meta={"nepali_title": title},
                    limit=limit_per_act
                )
                all_hits.extend(hits)
        else:
            # Fallback: simple unfiltered search
            hits = self.vector_store.search_collection(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit
            )
            all_hits.extend(hits)

        # Deduplicate hits
        seen_ids = set()
        deduped_hits = []
        for hit in all_hits:
            if hit["id"] not in seen_ids:
                seen_ids.add(hit["id"])
                deduped_hits.append(hit)

        # Sort the combined quota-balanced results by score descending to present best hits first
        deduped_hits.sort(key=lambda x: x["score"], reverse=True)
        return deduped_hits

    def build_context(self, hits: List[Dict[str, Any]]) -> str:
        """
        Transforms vector store hits into a beautifully structured XML/Markdown context block.
        Ensures each chunk has a distinct CITATION index for the LLM to refer back to.
        """
        if not hits:
            return "No matching legal references were found in the database."
            
        context_parts = []
        context_parts.append("=== STRUCTURED LEGAL REFERENCE CONTEXT ===")
        context_parts.append("Below are the exact law sections extracted from the official acts database. Use these references to construct your answer. Every fact you declare MUST cite its corresponding [CITATION index]!:\n")
        
        for idx, hit in enumerate(hits):
            payload = hit["payload"]
            citation = payload.get("citation", "अज्ञात सन्दर्भ")
            text = payload.get("text", "")
            raw_text = payload.get("raw_text", text)
            
            context_parts.append(f"--- [CITATION {idx + 1}] ---")
            context_parts.append(f"Source Reference: {citation}")
            context_parts.append(f"Law Content:\n{raw_text}")
            context_parts.append("-" * 30 + "\n")
            
        return "\n".join(context_parts)


