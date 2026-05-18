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
        Embeds query and retrieves top K matching chunks from Qdrant.
        """
        logger.info(f"Retrieving top {limit} relevant chunks for query: '{query}'...")
        query_vector = self.embedder.embed_query(query)
        if not query_vector:
            logger.error("Failed to generate embedding vector for the search query.")
            return []
            
        hits = self.vector_store.search_collection(
            collection_name=self.collection_name,
            query_vector=query_vector,
            filter_meta=filter_meta,
            limit=limit
        )
        return hits

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

if __name__ == "__main__":
    # Test query context retrieval
    logging.basicConfig(level=logging.INFO)
    builder = LegalContextBuilder()
    
    test_query = "नागरिकता सम्बन्धी के व्यवस्था छ?"
    hits = builder.retrieve_relevant_chunks(test_query, limit=3)
    
    print("\nRETRIEVED HITS:")
    for i, h in enumerate(hits):
        print(f"Hit {i+1} [Score {h['score']:.4f}]: {h['payload']['citation']}")
        
    context = builder.build_context(hits)
    print("\nGENERATED LLM CONTEXT:")
    print(context)
