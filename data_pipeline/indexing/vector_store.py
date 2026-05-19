import os
import sys
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models

# Load env credentials from data_pipeline/.env
env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.env"))
load_dotenv(env_path)

logger = logging.getLogger("vector_store")

class LegalVectorStore:
    """
    Interfaces with Qdrant Vector Database for index storage, update, and search retrieval.
    """
    def __init__(self):
        self.qdrant_url = os.getenv("QDRANT_URL")
        self.qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        if not self.qdrant_url or not self.qdrant_api_key:
            logger.error("Missing QDRANT_URL or QDRANT_API_KEY in environment.")
            raise ValueError("Qdrant credentials not configured in .env file.")
            
        logger.info(f"Connecting to remote Qdrant DB at {self.qdrant_url}...")
        self.client = QdrantClient(
            url=self.qdrant_url,
            api_key=self.qdrant_api_key,
            timeout=60
        )
        logger.info("Successfully connected to Qdrant DB.")

    def ensure_collection_exists(self, collection_name: str, vector_dimension: int) -> bool:
        """
        Checks if the collection exists, if not, creates it with Cosine similarity.
        """
        try:
            collections_res = self.client.get_collections()
            existing = [c.name for c in collections_res.collections]
            
            if collection_name in existing:
                logger.info(f"Collection '{collection_name}' already exists. Ensuring payload indexes exist...")
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="nepali_title",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="act_title",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                except Exception as ex:
                    logger.warning(f"Payload index creation check warning: {ex}")
                return True
                
            logger.info(f"Collection '{collection_name}' does not exist. Creating...")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_dimension,
                    distance=models.Distance.COSINE
                )
            )
            logger.info("Creating keyword payload indexes in Qdrant...")
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="nepali_title",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            self.client.create_payload_index(
                collection_name=collection_name,
                field_name="act_title",
                field_schema=models.PayloadSchemaType.KEYWORD
            )
            logger.info(f"Collection '{collection_name}' created successfully with payload indexes.")
            return True
        except Exception as e:
            logger.error(f"Failed to verify/create Qdrant collection: {e}")
            return False

    def upsert_chunks(self, collection_name: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> bool:
        """
        Upserts flat text chunks and their corresponding embeddings into the Qdrant database.
        """
        if not chunks or not embeddings:
            logger.warning("Empty chunks or embeddings. Skipping upsert.")
            return False
            
        if len(chunks) != len(embeddings):
            logger.error("Mismatched chunks and embeddings list sizes.")
            return False
            
        points = []
        import uuid
        
        for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            chunk_text = chunk["text"]
            # Standardize ID to a stable UUID based on chunk text
            stable_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_text))
            
            # Formulate payload combining chunk text and rich metadata
            payload = {
                "text": chunk_text,
                "raw_text": chunk["raw_text"],
                **chunk["metadata"]
            }
            
            points.append(
                models.PointStruct(
                    id=stable_uuid,
                    vector=vector,
                    payload=payload
                )
            )
            
        logger.info(f"Upserting {len(points)} points to collection '{collection_name}' in Qdrant...")
        
        # Batch upserting to prevent network timeout issues
        batch_size = 50
        for i in range(0, len(points), batch_size):
            batch = points[i : i + batch_size]
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
                logger.info(f"Upserted batch {i // batch_size + 1} ({len(batch)} points)")
            except Exception as e:
                logger.error(f"Failed to upsert batch starting at index {i}: {e}")
                return False
                
        logger.info("Vector store upsert completed successfully.")
        return True

    def search_collection(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        filter_meta: Optional[Dict[str, Any]] = None, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Executes vector search against a Qdrant collection with optional metadata filters.
        """
        qdrant_filter = None
        
        if filter_meta:
            must_filters = []
            for key, val in filter_meta.items():
                must_filters.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=val)
                    )
                )
            qdrant_filter = models.Filter(must=must_filters)
            
        try:
            search_results = self.client.query_points(
                collection_name=collection_name,
                query=query_vector,
                query_filter=qdrant_filter,
                limit=limit
            )
            
            hits = []
            for hit in search_results.points:
                hits.append({
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                })
            return hits
        except Exception as e:
            logger.error(f"Qdrant vector search failed: {e}")
            return []


