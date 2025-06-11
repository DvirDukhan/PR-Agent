"""Tests for vector store functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

# Skip tests if RedisVL is not available
pytest_plugins = []

try:
    from pr_verification_agent.core.vector_store import CodebaseVectorStore

    VECTOR_STORE_AVAILABLE = True
except ImportError:
    VECTOR_STORE_AVAILABLE = False
    CodebaseVectorStore = None


@pytest.mark.skipif(not VECTOR_STORE_AVAILABLE, reason="RedisVL not available")
class TestCodebaseVectorStore:
    """Test vector store functionality."""

    def test_schema_dict_structure(self):
        """Test that schema dictionary has correct structure."""
        store = CodebaseVectorStore()
        schema = store.schema_dict

        assert "index" in schema
        assert "fields" in schema
        assert schema["index"]["name"] == "pr_agent_codebase"
        assert schema["index"]["prefix"] == "codebase_docs"

        # Check for required fields
        field_names = [field["name"] for field in schema["fields"]]
        assert "file_path" in field_names
        assert "content" in field_names
        assert "content_vector" in field_names
        assert "language" in field_names

    def test_vector_field_configuration(self):
        """Test vector field has correct configuration."""
        store = CodebaseVectorStore()
        schema = store.schema_dict

        vector_field = None
        for field in schema["fields"]:
            if field["name"] == "content_vector":
                vector_field = field
                break

        assert vector_field is not None
        assert vector_field["type"] == "vector"
        assert vector_field["attrs"]["dims"] == 384
        assert vector_field["attrs"]["distance_metric"] == "cosine"
        assert vector_field["attrs"]["algorithm"] == "hnsw"

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.SearchIndex")
    def test_initialize_sync(self, mock_search_index, mock_vectorizer):
        """Test synchronous initialization."""
        # Setup mocks
        mock_vectorizer_instance = Mock()
        mock_vectorizer.return_value = mock_vectorizer_instance

        mock_index_instance = Mock()
        mock_search_index.return_value = mock_index_instance

        # Test initialization
        store = CodebaseVectorStore(use_async=False)
        store.initialize_sync()

        # Verify calls
        mock_vectorizer.assert_called_once_with(model="all-MiniLM-L6-v2")
        mock_search_index.assert_called_once()
        mock_index_instance.create.assert_called_once_with(overwrite=False)

        assert store.vectorizer == mock_vectorizer_instance
        assert store.index == mock_index_instance

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.AsyncSearchIndex")
    @pytest.mark.asyncio
    async def test_initialize_async(self, mock_async_search_index, mock_vectorizer):
        """Test asynchronous initialization."""
        # Setup mocks
        mock_vectorizer_instance = Mock()
        mock_vectorizer.return_value = mock_vectorizer_instance

        mock_index_instance = AsyncMock()
        mock_async_search_index.return_value = mock_index_instance

        # Test initialization
        store = CodebaseVectorStore(use_async=True)
        await store.initialize()

        # Verify calls
        mock_vectorizer.assert_called_once_with(model="all-MiniLM-L6-v2")
        mock_async_search_index.assert_called_once()
        mock_index_instance.create.assert_called_once_with(overwrite=False)

        assert store.vectorizer == mock_vectorizer_instance
        assert store.index == mock_index_instance

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.SearchIndex")
    def test_context_manager_sync(self, mock_search_index, mock_vectorizer):
        """Test synchronous context manager."""
        mock_vectorizer_instance = Mock()
        mock_vectorizer.return_value = mock_vectorizer_instance

        mock_index_instance = Mock()
        mock_search_index.return_value = mock_index_instance

        with CodebaseVectorStore(use_async=False) as store:
            assert store.vectorizer == mock_vectorizer_instance
            assert store.index == mock_index_instance

    def test_add_documents_not_initialized(self):
        """Test add_documents raises error when not initialized."""
        store = CodebaseVectorStore()

        with pytest.raises(RuntimeError, match="Vector store not initialized"):
            # This would be async in real usage, but we're testing the error condition
            import asyncio

            asyncio.run(store.add_documents([{"content": "test"}]))

    def test_search_not_initialized(self):
        """Test search raises error when not initialized."""
        store = CodebaseVectorStore()

        with pytest.raises(RuntimeError, match="Vector store not initialized"):
            import asyncio

            asyncio.run(store.search("test query"))

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.SearchIndex")
    @pytest.mark.asyncio
    async def test_add_documents_success(self, mock_search_index, mock_vectorizer):
        """Test successful document addition."""
        # Setup mocks
        mock_vectorizer_instance = Mock()
        mock_vectorizer_instance.embed.return_value = Mock()
        mock_vectorizer_instance.embed.return_value.tobytes.return_value = (
            b"fake_embedding"
        )
        mock_vectorizer.return_value = mock_vectorizer_instance

        mock_index_instance = Mock()
        mock_index_instance.load.return_value = ["doc1", "doc2"]
        mock_search_index.return_value = mock_index_instance

        # Test
        store = CodebaseVectorStore(use_async=False)
        store.initialize_sync()

        documents = [{"content": "test content 1"}, {"content": "test content 2"}]

        keys = await store.add_documents(documents)

        # Verify
        assert keys == ["doc1", "doc2"]
        mock_index_instance.load.assert_called_once()
        assert mock_vectorizer_instance.embed.call_count == 2

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.SearchIndex")
    @pytest.mark.asyncio
    async def test_search_success(self, mock_search_index, mock_vectorizer):
        """Test successful search."""
        # Setup mocks
        mock_vectorizer_instance = Mock()
        mock_vectorizer_instance.embed.return_value = Mock()
        mock_vectorizer.return_value = mock_vectorizer_instance

        mock_index_instance = Mock()
        mock_index_instance.query.return_value = [
            {"file_path": "test.py", "content": "test content", "vector_distance": 0.1}
        ]
        mock_search_index.return_value = mock_index_instance

        # Test
        store = CodebaseVectorStore(use_async=False)
        store.initialize_sync()

        results = await store.search("test query", limit=5)

        # Verify
        assert len(results) == 1
        assert results[0]["file_path"] == "test.py"
        mock_vectorizer_instance.embed.assert_called_once_with("test query")
        mock_index_instance.query.assert_called_once()

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.SearchIndex")
    @pytest.mark.asyncio
    async def test_get_stats(self, mock_search_index, mock_vectorizer):
        """Test getting vector store statistics."""
        # Setup mocks
        mock_vectorizer.return_value = Mock()

        mock_index_instance = Mock()
        mock_index_instance.info.return_value = {
            "num_docs": 100,
            "inverted_sz_mb": 5.2,
            "vector_index_sz_mb": 12.8,
        }
        mock_search_index.return_value = mock_index_instance

        # Test
        store = CodebaseVectorStore(use_async=False)
        store.initialize_sync()

        stats = await store.get_stats()

        # Verify
        assert stats["total_documents"] == 100
        assert stats["index_size_mb"] == 5.2
        assert stats["vector_index_size_mb"] == 12.8
        assert stats["index_name"] == "pr_agent_codebase"

    @patch("pr_verification_agent.core.vector_store.SentenceTransformerVectorizer")
    @patch("pr_verification_agent.core.vector_store.SearchIndex")
    @pytest.mark.asyncio
    async def test_clear(self, mock_search_index, mock_vectorizer):
        """Test clearing vector store."""
        # Setup mocks
        mock_vectorizer.return_value = Mock()

        mock_index_instance = Mock()
        mock_index_instance.clear.return_value = 50
        mock_search_index.return_value = mock_index_instance

        # Test
        store = CodebaseVectorStore(use_async=False)
        store.initialize_sync()

        count = await store.clear()

        # Verify
        assert count == 50
        mock_index_instance.clear.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_create_vector_store(self):
        """Test create_vector_store function."""
        from pr_verification_agent.core.vector_store import create_vector_store

        store = create_vector_store(use_async=False)
        assert isinstance(store, CodebaseVectorStore)
        assert not store.use_async

        store_async = create_vector_store(use_async=True)
        assert isinstance(store_async, CodebaseVectorStore)
        assert store_async.use_async
