"""Tests for repository functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

import pytest

from pr_verification_agent.core.repository import (
    RepositoryIndexer,
    CodeChunk,
    RepositoryError,
)


class TestCodeChunk:
    """Test CodeChunk functionality."""

    def test_code_chunk_creation(self):
        """Test creating a code chunk."""
        chunk = CodeChunk(
            content="def hello():\n    print('Hello, World!')",
            file_path="test.py",
            chunk_index=0,
            total_chunks=1,
            language="python",
            function_name="hello",
        )

        assert chunk.content == "def hello():\n    print('Hello, World!')"
        assert chunk.file_path == "test.py"
        assert chunk.chunk_index == 0
        assert chunk.total_chunks == 1
        assert chunk.language == "python"
        assert chunk.function_name == "hello"

    def test_code_chunk_to_dict(self):
        """Test converting code chunk to dictionary."""
        chunk = CodeChunk(
            content="test content",
            file_path="src/test.py",
            chunk_index=1,
            total_chunks=3,
            language="python",
            function_name="test_func",
            class_name="TestClass",
            imports="import os",
        )

        chunk_dict = chunk.to_dict()

        assert chunk_dict["file_path"] == "src/test.py"
        assert chunk_dict["file_name"] == "test.py"
        assert chunk_dict["file_extension"] == ".py"
        assert chunk_dict["language"] == "python"
        assert chunk_dict["chunk_index"] == 1
        assert chunk_dict["total_chunks"] == 3
        assert chunk_dict["content"] == "test content"
        assert chunk_dict["function_name"] == "test_func"
        assert chunk_dict["class_name"] == "TestClass"
        assert chunk_dict["imports"] == "import os"

    def test_code_chunk_get_hash(self):
        """Test getting content hash for change detection."""
        chunk = CodeChunk(
            content="test content",
            file_path="test.py",
            chunk_index=0,
            total_chunks=1,
            language="python",
        )

        hash1 = chunk.get_hash()
        assert isinstance(hash1, str)
        assert len(hash1) == 32  # MD5 hash length

        # Same content should produce same hash
        chunk2 = CodeChunk(
            content="test content",
            file_path="test.py",
            chunk_index=0,
            total_chunks=1,
            language="python",
        )
        hash2 = chunk2.get_hash()
        assert hash1 == hash2

        # Different content should produce different hash
        chunk3 = CodeChunk(
            content="different content",
            file_path="test.py",
            chunk_index=0,
            total_chunks=1,
            language="python",
        )
        hash3 = chunk3.get_hash()
        assert hash1 != hash3


class TestRepositoryIndexer:
    """Test RepositoryIndexer functionality."""

    def test_repository_indexer_creation(self):
        """Test creating a repository indexer."""
        indexer = RepositoryIndexer()
        assert indexer.repo_path == Path.cwd().resolve()

        custom_path = "/tmp/test"
        indexer_custom = RepositoryIndexer(custom_path)
        assert indexer_custom.repo_path == Path(custom_path).resolve()

    @patch("pr_verification_agent.core.repository.git.Repo")
    def test_validate_repository_success(self, mock_repo):
        """Test successful repository validation."""
        mock_repo.return_value = Mock()

        indexer = RepositoryIndexer()
        result = indexer.validate_repository()

        assert result is True
        mock_repo.assert_called_once_with(indexer.repo_path)

    @patch("pr_verification_agent.core.repository.git.Repo")
    def test_validate_repository_failure(self, mock_repo):
        """Test repository validation failure."""
        from git.exc import InvalidGitRepositoryError

        mock_repo.side_effect = InvalidGitRepositoryError()

        indexer = RepositoryIndexer()

        with pytest.raises(RepositoryError, match="No Git repository found"):
            indexer.validate_repository()

    def test_detect_language(self):
        """Test language detection from file extensions."""
        indexer = RepositoryIndexer()

        assert indexer._detect_language(Path("test.py")) == "python"
        assert indexer._detect_language(Path("test.js")) == "javascript"
        assert indexer._detect_language(Path("test.java")) == "java"
        assert indexer._detect_language(Path("test.cpp")) == "cpp"
        assert indexer._detect_language(Path("test.unknown")) == "unknown"

    def test_is_binary_file(self):
        """Test binary file detection."""
        indexer = RepositoryIndexer()

        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is a text file")
            text_file = Path(f.name)

        try:
            assert not indexer._is_binary_file(text_file)
        finally:
            text_file.unlink()

        # Create temporary binary file
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".bin", delete=False) as f:
            f.write(b"\x00\x01\x02\x03")
            binary_file = Path(f.name)

        try:
            assert indexer._is_binary_file(binary_file)
        finally:
            binary_file.unlink()

    def test_extract_function_name_python(self):
        """Test extracting function names from Python code."""
        indexer = RepositoryIndexer()

        python_code = """
def hello_world():
    print("Hello, World!")
    
def another_function(param1, param2):
    return param1 + param2
"""

        function_name = indexer._extract_function_name(python_code, "python")
        assert function_name == "hello_world"

    def test_extract_function_name_javascript(self):
        """Test extracting function names from JavaScript code."""
        indexer = RepositoryIndexer()

        js_code = """
function calculateSum(a, b) {
    return a + b;
}
"""

        function_name = indexer._extract_function_name(js_code, "javascript")
        assert function_name == "calculateSum"

    def test_extract_class_name_python(self):
        """Test extracting class names from Python code."""
        indexer = RepositoryIndexer()

        python_code = """
class MyTestClass:
    def __init__(self):
        pass
"""

        class_name = indexer._extract_class_name(python_code, "python")
        assert class_name == "MyTestClass"

    def test_extract_imports_python(self):
        """Test extracting import statements from Python code."""
        indexer = RepositoryIndexer()

        python_code = """
import os
import sys
from pathlib import Path
from typing import Dict, List

def some_function():
    pass
"""

        imports = indexer._extract_imports(python_code, "python")
        assert "import os" in imports
        assert "import sys" in imports
        assert "from pathlib import Path" in imports
        assert "from typing import Dict, List" in imports

    def test_chunk_file_content(self):
        """Test chunking file content."""
        indexer = RepositoryIndexer()

        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                """
import os
import sys

def function1():
    print("Function 1")
    
def function2():
    print("Function 2")
    
class TestClass:
    def method1(self):
        pass
"""
            )
            temp_file = Path(f.name)

        try:
            chunks = indexer.chunk_file_content(temp_file)

            assert len(chunks) > 0
            for chunk in chunks:
                assert isinstance(chunk, CodeChunk)
                assert chunk.language == "python"
                assert chunk.total_chunks == len(chunks)

        finally:
            temp_file.unlink()

    @patch(
        "pr_verification_agent.core.repository.RepositoryIndexer.validate_repository"
    )
    @patch("pr_verification_agent.core.repository.CodebaseVectorStore")
    @patch("pr_verification_agent.core.repository.RepositoryIndexer.discover_files")
    @patch("pr_verification_agent.core.repository.RepositoryIndexer.chunk_file_content")
    @pytest.mark.asyncio
    async def test_index_repository(
        self, mock_chunk_content, mock_discover, mock_vector_store, mock_validate
    ):
        """Test repository indexing process."""
        # Setup mocks
        mock_validate.return_value = True
        mock_discover.return_value = [Path("test1.py"), Path("test2.py")]

        mock_chunk1 = Mock(spec=CodeChunk)
        mock_chunk1.to_dict.return_value = {"content": "chunk1"}
        mock_chunk2 = Mock(spec=CodeChunk)
        mock_chunk2.to_dict.return_value = {"content": "chunk2"}

        mock_chunk_content.side_effect = [[mock_chunk1], [mock_chunk2]]

        mock_store_instance = AsyncMock()
        mock_store_instance.add_documents.return_value = ["doc1", "doc2"]
        mock_vector_store.return_value = mock_store_instance

        # Test indexing
        indexer = RepositoryIndexer()
        stats = await indexer.index_repository()

        # Verify results
        assert stats["total_files"] == 2
        assert stats["total_chunks"] == 2
        assert "repository_path" in stats
        assert "index_name" in stats

        # Verify method calls
        mock_validate.assert_called_once()
        mock_discover.assert_called_once()
        assert mock_chunk_content.call_count == 2
        mock_store_instance.initialize.assert_called_once()
        mock_store_instance.add_documents.assert_called_once()


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_get_repository_indexer(self):
        """Test get_repository_indexer function."""
        from pr_verification_agent.core.repository import get_repository_indexer

        indexer = get_repository_indexer()
        assert isinstance(indexer, RepositoryIndexer)

        custom_indexer = get_repository_indexer("/tmp/test")
        assert isinstance(custom_indexer, RepositoryIndexer)
        assert custom_indexer.repo_path == Path("/tmp/test").resolve()
