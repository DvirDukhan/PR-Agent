"""Vector store implementation using RedisVL for codebase indexing and search."""

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
from redisvl.index import AsyncSearchIndex, SearchIndex
from redisvl.query import VectorQuery, FilterQuery
from redisvl.schema import IndexSchema
from redisvl.vectorizers import SentenceTransformerVectorizer

from .config import config
from .logging import get_logger

logger = get_logger(__name__)


class CodebaseVectorStore:
    """Vector store for codebase indexing and semantic search using RedisVL."""
    
    def __init__(self, use_async: bool = False):
        """Initialize the vector store.
        
        Args:
            use_async: Whether to use async Redis client
        """
        self.use_async = use_async
        self.config = config
        self.vectorizer = None
        self.index = None
        self._schema = None
        
    @property
    def schema_dict(self) -> Dict[str, Any]:
        """Get the RedisVL schema definition for codebase indexing."""
        return {
            "index": {
                "name": self.config.repository.index_name,
                "prefix": self.config.repository.index_prefix,
            },
            "fields": [
                # Metadata fields
                {"name": "file_path", "type": "text"},
                {"name": "file_name", "type": "tag"},
                {"name": "file_extension", "type": "tag"},
                {"name": "language", "type": "tag"},
                {"name": "chunk_index", "type": "numeric"},
                {"name": "total_chunks", "type": "numeric"},
                
                # Content fields
                {"name": "content", "type": "text"},
                {"name": "function_name", "type": "tag"},
                {"name": "class_name", "type": "tag"},
                {"name": "imports", "type": "text"},
                
                # Timestamps
                {"name": "created_at", "type": "numeric"},
                {"name": "updated_at", "type": "numeric"},
                
                # Vector field
                {
                    "name": "content_vector",
                    "type": "vector",
                    "attrs": {
                        "dims": self.config.repository.vector_dims,
                        "distance_metric": self.config.repository.distance_metric,
                        "algorithm": self.config.repository.vector_algorithm,
                        "datatype": "float32"
                    }
                }
            ]
        }
    
    async def initialize(self) -> None:
        """Initialize the vector store and create index if needed."""
        try:
            # Initialize vectorizer
            self.vectorizer = SentenceTransformerVectorizer(
                model=self.config.repository.embedding_model
            )
            
            # Create schema
            self._schema = IndexSchema.from_dict(self.schema_dict)
            
            # Create index
            if self.use_async:
                self.index = AsyncSearchIndex(
                    schema=self._schema,
                    redis_url=self.config.redis.connection_url
                )
            else:
                self.index = SearchIndex(
                    schema=self._schema,
                    redis_url=self.config.redis.connection_url
                )
            
            # Create the index in Redis (if it doesn't exist)
            if self.use_async:
                await self.index.create(overwrite=False)
            else:
                self.index.create(overwrite=False)
                
            logger.info(
                "Vector store initialized",
                index_name=self.config.repository.index_name,
                vectorizer=self.config.repository.embedding_model
            )
            
        except Exception as e:
            logger.error("Failed to initialize vector store", error=str(e))
            raise
    
    def initialize_sync(self) -> None:
        """Synchronous version of initialize."""
        if self.use_async:
            asyncio.run(self.initialize())
        else:
            # Run the async parts synchronously
            self.vectorizer = SentenceTransformerVectorizer(
                model=self.config.repository.embedding_model
            )
            
            self._schema = IndexSchema.from_dict(self.schema_dict)
            
            self.index = SearchIndex(
                schema=self._schema,
                redis_url=self.config.redis.connection_url
            )
            
            self.index.create(overwrite=False)
            
            logger.info(
                "Vector store initialized (sync)",
                index_name=self.config.repository.index_name
            )
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries with content and metadata
            
        Returns:
            List of document IDs that were added
        """
        if not self.index or not self.vectorizer:
            raise RuntimeError("Vector store not initialized")
        
        # Generate embeddings for documents
        processed_docs = []
        for doc in documents:
            # Create embedding for content
            content = doc.get("content", "")
            if content:
                embedding = self.vectorizer.embed(content)
                doc["content_vector"] = embedding.tobytes()
            
            processed_docs.append(doc)
        
        # Load documents to Redis
        if self.use_async:
            keys = await self.index.load(processed_docs)
        else:
            keys = self.index.load(processed_docs)
        
        logger.info(f"Added {len(keys)} documents to vector store")
        return keys
    
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        return_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            filters: Optional filters to apply
            return_fields: Fields to return in results
            
        Returns:
            List of matching documents with scores
        """
        if not self.index or not self.vectorizer:
            raise RuntimeError("Vector store not initialized")
        
        # Generate query embedding
        query_embedding = self.vectorizer.embed(query)
        
        # Default return fields
        if return_fields is None:
            return_fields = [
                "file_path", "file_name", "language", "content",
                "function_name", "class_name", "vector_distance"
            ]
        
        # Create vector query
        vector_query = VectorQuery(
            vector=query_embedding,
            vector_field_name="content_vector",
            return_fields=return_fields,
            num_results=limit
        )
        
        # Apply filters if provided
        if filters:
            # Convert filters to RedisVL filter format
            # This is a simplified implementation
            for field, value in filters.items():
                if isinstance(value, str):
                    vector_query = vector_query.filter(f"{field}=={value}")
        
        # Execute search
        if self.use_async:
            results = await self.index.query(vector_query)
        else:
            results = self.index.query(vector_query)
        
        logger.info(f"Vector search returned {len(results)} results")
        return results
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        if not self.index:
            raise RuntimeError("Vector store not initialized")
        
        try:
            if self.use_async:
                stats = await self.index.info()
            else:
                stats = self.index.info()
            
            return {
                "index_name": self.config.repository.index_name,
                "total_documents": stats.get("num_docs", 0),
                "index_size_mb": stats.get("inverted_sz_mb", 0),
                "vector_index_size_mb": stats.get("vector_index_sz_mb", 0),
            }
        except Exception as e:
            logger.error("Failed to get vector store stats", error=str(e))
            return {}
    
    async def clear(self) -> int:
        """Clear all documents from the vector store.
        
        Returns:
            Number of documents cleared
        """
        if not self.index:
            raise RuntimeError("Vector store not initialized")
        
        if self.use_async:
            count = await self.index.clear()
        else:
            count = self.index.clear()
        
        logger.info(f"Cleared {count} documents from vector store")
        return count
    
    async def delete_index(self) -> None:
        """Delete the entire index."""
        if not self.index:
            raise RuntimeError("Vector store not initialized")
        
        if self.use_async:
            await self.index.delete()
        else:
            self.index.delete()
        
        logger.info("Deleted vector store index")
    
    def __enter__(self):
        """Context manager entry."""
        if not self.use_async:
            self.initialize_sync()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass


# Convenience functions
def create_vector_store(use_async: bool = False) -> CodebaseVectorStore:
    """Create a new vector store instance."""
    return CodebaseVectorStore(use_async=use_async)


async def search_codebase(
    query: str,
    limit: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """Convenience function for searching the codebase."""
    async with CodebaseVectorStore(use_async=True) as store:
        return await store.search(query, limit=limit, filters=filters)
