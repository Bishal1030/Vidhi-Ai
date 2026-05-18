import os
import sys
import logging
import argparse
import time
from typing import List, Dict, Any

# Add workspace to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from data_pipeline.ingestion.config import STRUCTURED_ACTS_DIR, INGESTION_LOG
from data_pipeline.indexing.chunker import chunk_file
from data_pipeline.indexing.embedder import LegalEmbedder
from data_pipeline.indexing.vector_store import LegalVectorStore

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(INGESTION_LOG, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("index_builder")

class LegalIndexBuilder:
    """
    Orchestrates the conversion of structured legal JSON documents into RAG vector indexes
    stored in Qdrant.
    """
    def __init__(self, collection_name: str = "vidhi_legal_acts", use_openai: bool = False):
        self.collection_name = collection_name
        self.embedder = LegalEmbedder(use_openai=use_openai)
        self.vector_store = LegalVectorStore()
        
    def build_index_for_file(self, json_path: str) -> bool:
        """
        Processes a single structured JSON file, chunks it, generates embeddings,
        and saves it to Qdrant.
        """
        logger.info("=========================================================")
        logger.info(f"BUILDING SEARCH INDEX FOR: {os.path.basename(json_path)}")
        logger.info("=========================================================")
        
        start_time = time.time()
        
        # Step 1: Hierarchical Chunking
        logger.info("Step 1: Splitting legal act into semantic chunks...")
        chunks = chunk_file(json_path)
        if not chunks:
            logger.error("Failed to generate semantic chunks from JSON file.")
            return False
            
        logger.info(f"Generated {len(chunks)} chunks with parent legal citations.")
        
        # Step 2: Ensure Qdrant collection exists (delete and recreate to clear stale/misspelled points)
        logger.info("Step 2: Preparing remote vector store collection (recreating to purge old entries)...")
        try:
            self.vector_store.client.delete_collection(self.collection_name)
            logger.info(f"Purged stale collection '{self.collection_name}' from Qdrant.")
        except Exception as delete_err:
            logger.warning(f"Could not delete collection (may not exist yet): {delete_err}")
            
        dim = self.embedder.get_embedding_dimension()
        if not self.vector_store.ensure_collection_exists(self.collection_name, dim):
            logger.error(f"Failed to verify/create Qdrant collection '{self.collection_name}'.")
            return False
            
        # Step 3: Embed chunks in batches
        logger.info("Step 3: Generating dense vector embeddings in batches...")
        texts = [chunk["text"] for chunk in chunks]
        embeddings = []
        
        batch_size = 32
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                batch_embeddings = self.embedder.embed_texts(batch)
                embeddings.extend(batch_embeddings)
                logger.info(f"Embedded batch {i // batch_size + 1} / {len(texts) // batch_size + 1}...")
            except Exception as e:
                logger.error(f"Failed batch embedding generation starting at index {i}: {e}")
                return False
                
        # Step 4: Upsert to Qdrant
        logger.info("Step 4: Upserting vectors and legal payloads to Qdrant...")
        success = self.vector_store.upsert_chunks(
            collection_name=self.collection_name,
            chunks=chunks,
            embeddings=embeddings
        )
        
        if success:
            duration = time.time() - start_time
            logger.info(f"SEARCH INDEX BUILT SUCCESSFULLY!")
            logger.info(f"   - Collection:  {self.collection_name}")
            logger.info(f"   - Chunks Indexed: {len(chunks)}")
            logger.info(f"   - Duration:    {duration:.2f} seconds")
            return True
        else:
            logger.error("Failed to index all points to vector database.")
            return False

    def build_full_index(self) -> bool:
        """Indexes all structured JSON files in the output directory."""
        if not os.path.exists(STRUCTURED_ACTS_DIR):
            logger.error(f"Structured acts folder does not exist: {STRUCTURED_ACTS_DIR}")
            return False
            
        json_files = [f for f in os.listdir(STRUCTURED_ACTS_DIR) if f.endswith(".json")]
        if not json_files:
            logger.warning(f"No structured JSON files found in {STRUCTURED_ACTS_DIR}.")
            return False
            
        logger.info(f"Found {len(json_files)} structured acts ready for index building.")
        
        all_success = True
        for json_file in json_files:
            full_path = os.path.join(STRUCTURED_ACTS_DIR, json_file)
            success = self.build_index_for_file(full_path)
            if not success:
                all_success = False
                
        return all_success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vidhi-Ai Legal Search Index Builder")
    parser.add_argument("--collection", type=str, default="vidhi_legal_acts", help="Qdrant collection name")
    parser.add_argument("--openai", action="store_true", help="Use OpenAI text-embedding-3-small embeddings")
    args = parser.parse_args()
    
    builder = LegalIndexBuilder(collection_name=args.collection, use_openai=args.openai)
    builder.build_full_index()
