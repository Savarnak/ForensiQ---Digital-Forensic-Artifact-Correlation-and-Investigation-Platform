from app.core.config import settings
from app.core.logging import logger
from typing import List, Dict, Any, Optional

try:
    from qdrant_client import QdrantClient as SyncQdrantClient
    from qdrant_client.http.models import Distance, VectorParams
    HAS_QDRANT = True
except ImportError:
    SyncQdrantClient = None
    Distance = None
    VectorParams = None
    HAS_QDRANT = False

COLLECTION_NAME = "argus_evidence_vectors"

class QdrantClientWrapper:
    def __init__(self):
        self.client = None
        self.connected = False

    def connect(self):
        if not HAS_QDRANT:
            logger.info("Qdrant client package not installed. Operating in vector-emulated mode.")
            self.connected = False
            return
        try:
            self.client = SyncQdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None,
                timeout=3.0
            )
            collections = self.client.get_collections()
            self.connected = True
            logger.info("Successfully connected to Qdrant Vector DB.")
            self._ensure_collection()
        except Exception as e:
            logger.warning(f"Qdrant connection unavailable ({e}). Falling back to vector-emulated mode.")
            self.connected = False

    def _ensure_collection(self):
        if not self.connected or not self.client:
            return
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if COLLECTION_NAME not in collections:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
        except Exception as err:
            logger.warning(f"Failed to verify/create Qdrant collection: {err}")

    def upsert_vectors(self, points: List[Dict[str, Any]]):
        if not self.connected or not self.client:
            logger.debug(f"[Emulated Qdrant] Upserted {len(points)} vector points.")
            return
        try:
            self.client.upsert(collection_name=COLLECTION_NAME, points=points)
        except Exception as e:
            logger.error(f"Failed to upsert to Qdrant: {e}")

    def search_similar(self, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        if not self.connected or not self.client:
            logger.debug("[Emulated Qdrant] Vector search returned empty list.")
            return []
        try:
            hits = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit
            )
            return [hit.dict() for hit in hits]
        except Exception as e:
            logger.error(f"Failed to search Qdrant: {e}")
            return []

qdrant_client = QdrantClientWrapper()
