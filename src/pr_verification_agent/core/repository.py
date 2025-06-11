"""Repository discovery, parsing, and indexing functionality."""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterator
import hashlib

import git
from git.exc import InvalidGitRepositoryError

from .config import config
from .logging import get_logger
from .vector_store import CodebaseVectorStore

logger = get_logger(__name__)


class RepositoryError(Exception):
    """Base exception for repository operations."""
    pass


class CodeChunk:
    """Represents a chunk of code with metadata."""
    
    def __init__(
        self,
        content: str,
        file_path: str,
        chunk_index: int,
        total_chunks: int,
        language: str,
        function_name: Optional[str] = None,
        class_name: Optional[str] = None,
        imports: Optional[str] = None
    ):
        self.content = content
        self.file_path = file_path
        self.chunk_index = chunk_index
        self.total_chunks = total_chunks
        self.language = language
        self.function_name = function_name
        self.class_name = class_name
        self.imports = imports
        self.created_at = time.time()
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for vector store."""
        file_path = Path(self.file_path)
        return {
            "file_path": str(self.file_path),
            "file_name": file_path.name,
            "file_extension": file_path.suffix,
            "language": self.language,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "content": self.content,
            "function_name": self.function_name or "",
            "class_name": self.class_name or "",
            "imports": self.imports or "",
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    def get_hash(self) -> str:
        """Get content hash for change detection."""
        content_str = f"{self.file_path}:{self.chunk_index}:{self.content}"
        return hashlib.md5(content_str.encode()).hexdigest()


class RepositoryIndexer:
    """Handles repository discovery, parsing, and indexing."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize repository indexer.
        
        Args:
            repo_path: Path to repository. If None, uses current directory.
        """
        self.repo_path = Path(repo_path or os.getcwd()).resolve()
        self.config = config
        self.vector_store = None
        self._repo = None
        
    def validate_repository(self) -> bool:
        """Validate that the path contains a Git repository.
        
        Returns:
            True if valid Git repository
            
        Raises:
            RepositoryError: If not a valid repository
        """
        try:
            self._repo = git.Repo(self.repo_path)
            logger.info(f"Found Git repository at {self.repo_path}")
            return True
        except InvalidGitRepositoryError:
            raise RepositoryError(f"No Git repository found at {self.repo_path}")
    
    def discover_files(self) -> List[Path]:
        """Discover code files in the repository.
        
        Returns:
            List of file paths to index
        """
        files = []
        excluded_dirs = set(self.config.repository.excluded_dirs_list)
        included_extensions = set(self.config.repository.included_extensions_list)
        max_size_bytes = self.config.repository.max_file_size_mb * 1024 * 1024
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Check file extension
                if file_path.suffix not in included_extensions:
                    continue
                
                # Check file size
                try:
                    if file_path.stat().st_size > max_size_bytes:
                        logger.warning(f"Skipping large file: {file_path}")
                        continue
                except OSError:
                    continue
                
                # Check if file is binary
                if self._is_binary_file(file_path):
                    continue
                
                files.append(file_path)
        
        logger.info(f"Discovered {len(files)} files for indexing")
        return files
    
    def _is_binary_file(self, file_path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except (OSError, UnicodeDecodeError):
            return True
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
        }
        return extension_map.get(file_path.suffix.lower(), 'unknown')
    
    def chunk_file_content(self, file_path: Path) -> List[CodeChunk]:
        """Chunk file content into manageable pieces.
        
        Args:
            file_path: Path to the file to chunk
            
        Returns:
            List of code chunks
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            logger.warning(f"Failed to read file {file_path}: {e}")
            return []
        
        if not content.strip():
            return []
        
        language = self._detect_language(file_path)
        chunk_size = self.config.repository.chunk_size
        chunk_overlap = self.config.repository.chunk_overlap
        
        # Simple chunking by lines for now
        # TODO: Implement language-aware chunking using tree-sitter
        lines = content.split('\n')
        chunks = []
        
        # Calculate approximate lines per chunk
        avg_line_length = len(content) / len(lines) if lines else 50
        lines_per_chunk = max(1, int(chunk_size / avg_line_length))
        overlap_lines = max(0, int(chunk_overlap / avg_line_length))
        
        start_idx = 0
        chunk_index = 0
        
        while start_idx < len(lines):
            end_idx = min(start_idx + lines_per_chunk, len(lines))
            chunk_lines = lines[start_idx:end_idx]
            chunk_content = '\n'.join(chunk_lines)
            
            if chunk_content.strip():
                # Extract basic metadata (simplified)
                function_name = self._extract_function_name(chunk_content, language)
                class_name = self._extract_class_name(chunk_content, language)
                imports = self._extract_imports(chunk_content, language)
                
                chunk = CodeChunk(
                    content=chunk_content,
                    file_path=str(file_path.relative_to(self.repo_path)),
                    chunk_index=chunk_index,
                    total_chunks=0,  # Will be updated later
                    language=language,
                    function_name=function_name,
                    class_name=class_name,
                    imports=imports
                )
                chunks.append(chunk)
                chunk_index += 1
            
            # Move to next chunk with overlap
            start_idx = end_idx - overlap_lines
            if start_idx >= end_idx:
                break
        
        # Update total_chunks for all chunks
        for chunk in chunks:
            chunk.total_chunks = len(chunks)
        
        return chunks
    
    def _extract_function_name(self, content: str, language: str) -> Optional[str]:
        """Extract function name from code chunk (simplified)."""
        # This is a very basic implementation
        # TODO: Use tree-sitter for proper parsing
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if language == 'python' and line.startswith('def '):
                return line.split('(')[0].replace('def ', '').strip()
            elif language in ['javascript', 'typescript'] and 'function ' in line:
                parts = line.split('function ')
                if len(parts) > 1:
                    return parts[1].split('(')[0].strip()
        return None
    
    def _extract_class_name(self, content: str, language: str) -> Optional[str]:
        """Extract class name from code chunk (simplified)."""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if language == 'python' and line.startswith('class '):
                return line.split('(')[0].replace('class ', '').strip(':')
            elif language in ['java', 'csharp'] and 'class ' in line:
                parts = line.split('class ')
                if len(parts) > 1:
                    return parts[1].split()[0].strip()
        return None
    
    def _extract_imports(self, content: str, language: str) -> Optional[str]:
        """Extract import statements from code chunk (simplified)."""
        lines = content.split('\n')
        imports = []
        for line in lines:
            line = line.strip()
            if language == 'python' and (line.startswith('import ') or line.startswith('from ')):
                imports.append(line)
            elif language in ['javascript', 'typescript'] and line.startswith('import '):
                imports.append(line)
        return '; '.join(imports) if imports else None
    
    async def index_repository(self, force_reindex: bool = False) -> Dict[str, int]:
        """Index the entire repository.
        
        Args:
            force_reindex: Whether to force reindexing even if up to date
            
        Returns:
            Dictionary with indexing statistics
        """
        logger.info(f"Starting repository indexing: {self.repo_path}")
        
        # Validate repository
        self.validate_repository()
        
        # Initialize vector store
        self.vector_store = CodebaseVectorStore(use_async=True)
        await self.vector_store.initialize()
        
        # Discover files
        files = self.discover_files()
        
        # Process files in batches
        batch_size = self.config.repository.index_batch_size
        total_chunks = 0
        total_files = 0
        
        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            batch_chunks = []
            
            for file_path in batch_files:
                chunks = self.chunk_file_content(file_path)
                batch_chunks.extend(chunks)
                if chunks:
                    total_files += 1
            
            if batch_chunks:
                # Convert chunks to documents
                documents = [chunk.to_dict() for chunk in batch_chunks]
                
                # Add to vector store
                await self.vector_store.add_documents(documents)
                total_chunks += len(batch_chunks)
                
                logger.info(
                    f"Indexed batch {i//batch_size + 1}/{(len(files) + batch_size - 1)//batch_size}: "
                    f"{len(batch_chunks)} chunks from {len(batch_files)} files"
                )
        
        stats = {
            "total_files": total_files,
            "total_chunks": total_chunks,
            "repository_path": str(self.repo_path),
            "index_name": self.config.repository.index_name,
        }
        
        logger.info(f"Repository indexing completed: {stats}")
        return stats


# Convenience functions
def get_repository_indexer(repo_path: Optional[str] = None) -> RepositoryIndexer:
    """Get a repository indexer instance."""
    return RepositoryIndexer(repo_path)


async def index_current_repository(force_reindex: bool = False) -> Dict[str, int]:
    """Index the current repository."""
    indexer = RepositoryIndexer()
    return await indexer.index_repository(force_reindex=force_reindex)
