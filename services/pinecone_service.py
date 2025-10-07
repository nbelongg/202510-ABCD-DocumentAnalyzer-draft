"""Pinecone service for vector search and retrieval"""
from typing import List, Dict, Optional
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langsmith import traceable
from config.settings import settings
from services.logger import get_logger
from services.exceptions import PineconeError

logger = get_logger(__name__)


class PineconeService:
    """Service for Pinecone vector database operations"""
    
    def __init__(self):
        """Initialize Pinecone client"""
        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            logger.info(
                "pinecone_initialized",
                index_name=settings.PINECONE_INDEX_NAME
            )
        except Exception as e:
            logger.error("pinecone_initialization_failed", error=str(e))
            raise PineconeError(f"Failed to initialize Pinecone: {str(e)}")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text"""
        try:
            return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error("embedding_generation_failed", error=str(e))
            raise PineconeError(f"Failed to generate embedding: {str(e)}")
    
    @traceable(name="query_vectors", tags=["pinecone", "search"])
    def query(
        self,
        query_text: str,
        top_k: int = 10,
        filter: Optional[Dict] = None,
        include_metadata: bool = True
    ) -> List[Dict]:
        """
        Query Pinecone for similar vectors
        
        Args:
            query_text: Query text
            top_k: Number of results to return
            filter: Metadata filters
            include_metadata: Include metadata in results
            
        Returns:
            List of matches with scores and metadata
        """
        try:
            logger.info(
                "querying_pinecone",
                query_length=len(query_text),
                top_k=top_k,
                filter=filter
            )
            
            query_embedding = self._generate_embedding(query_text)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                filter=filter,
                include_metadata=include_metadata
            )
            
            matches = []
            for match in results.get("matches", []):
                matches.append({
                    "id": match.get("id"),
                    "score": match.get("score"),
                    "text": match.get("metadata", {}).get("text", ""),
                    "source": match.get("metadata", {}).get("source", ""),
                    "metadata": match.get("metadata", {})
                })
            
            logger.info(
                "pinecone_query_success",
                num_matches=len(matches)
            )
            
            return matches
            
        except Exception as e:
            logger.error("pinecone_query_failed", error=str(e))
            raise PineconeError(f"Pinecone query failed: {str(e)}")
    
    @traceable(name="fetch_chunks_by_topic", tags=["pinecone", "search"])
    def fetch_chunks_by_topic(
        self,
        query: str,
        topic: str,
        num_examples: int = 10
    ) -> List[Dict[str, str]]:
        """
        Fetch relevant chunks filtered by topic
        
        Args:
            query: Search query
            topic: Topic to filter by
            num_examples: Number of examples to return
            
        Returns:
            List of dictionaries with 'comment' and 'sources'
        """
        try:
            filter_dict = None if topic == "Overall" else {"Topic": {"$eq": topic}}
            
            matches = self.query(
                query_text=query,
                top_k=num_examples,
                filter=filter_dict
            )
            
            # Format for legacy compatibility
            results = []
            for match in matches:
                results.append({
                    "comment": match["text"],
                    "sources": match["source"]
                })
            
            return results
            
        except Exception as e:
            logger.error("fetch_chunks_failed", error=str(e), topic=topic)
            raise PineconeError(f"Failed to fetch chunks: {str(e)}")
    
    @traceable(name="upsert_vectors", tags=["pinecone", "write"])
    def upsert(
        self,
        vectors: List[tuple],
        namespace: Optional[str] = None
    ) -> Dict:
        """
        Upsert vectors to Pinecone
        
        Args:
            vectors: List of (id, embedding, metadata) tuples
            namespace: Optional namespace
            
        Returns:
            Upsert response
        """
        try:
            logger.info("upserting_vectors", count=len(vectors))
            
            response = self.index.upsert(
                vectors=vectors,
                namespace=namespace
            )
            
            logger.info("upsert_success", upserted_count=response.get("upserted_count"))
            return response
            
        except Exception as e:
            logger.error("upsert_failed", error=str(e))
            raise PineconeError(f"Upsert failed: {str(e)}")

