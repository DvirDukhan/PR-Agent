"""Tests for state management functionality."""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timezone

# Skip tests if state manager is not available
pytest_plugins = []

try:
    from pr_verification_agent.core.state_manager import (
        StateManager, ChangeDetector, ContentHasher,
        TicketState, PRState, AnalysisResult, StateType
    )
    STATE_MANAGER_AVAILABLE = True
except ImportError:
    STATE_MANAGER_AVAILABLE = False
    StateManager = None


@pytest.mark.skipif(not STATE_MANAGER_AVAILABLE, reason="State manager not available")
class TestContentHasher:
    """Test content hashing functionality."""

    def test_hash_content_string(self):
        """Test hashing string content."""
        content = "test content"
        hash1 = ContentHasher.hash_content(content)
        hash2 = ContentHasher.hash_content(content)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        assert isinstance(hash1, str)

    def test_hash_content_different_strings(self):
        """Test that different strings produce different hashes."""
        hash1 = ContentHasher.hash_content("content1")
        hash2 = ContentHasher.hash_content("content2")
        
        assert hash1 != hash2

    def test_hash_dod_content(self):
        """Test DoD content hashing."""
        dod_text = "Definition of Done"
        requirements = ["req1", "req2"]
        
        hash1 = ContentHasher.hash_dod_content(dod_text, requirements)
        hash2 = ContentHasher.hash_dod_content(dod_text, requirements)
        
        assert hash1 == hash2

    def test_hash_dod_content_order_independence(self):
        """Test that requirement order doesn't affect hash."""
        dod_text = "Definition of Done"
        req1 = ["req1", "req2"]
        req2 = ["req2", "req1"]
        
        hash1 = ContentHasher.hash_dod_content(dod_text, req1)
        hash2 = ContentHasher.hash_dod_content(dod_text, req2)
        
        assert hash1 == hash2

    def test_hash_pr_content(self):
        """Test PR content hashing."""
        files = [{"filename": "file1.py"}, {"filename": "file2.py"}]
        commits = ["commit1", "commit2"]
        
        hash1 = ContentHasher.hash_pr_content(files, commits)
        hash2 = ContentHasher.hash_pr_content(files, commits)
        
        assert hash1 == hash2


@pytest.mark.skipif(not STATE_MANAGER_AVAILABLE, reason="State manager not available")
class TestAnalysisResult:
    """Test analysis result data structure."""

    def test_analysis_result_creation(self):
        """Test creating analysis result."""
        result = AnalysisResult(
            score=85.0,
            issues=[{"type": "missing", "description": "test"}],
            recommendations=[{"action": "add", "description": "test"}],
            confidence=0.92,
            timestamp="2024-01-15T10:30:00Z"
        )
        
        assert result.score == 85.0
        assert result.confidence == 0.92
        assert result.analyzer_version == "0.1.0"
        assert len(result.issues) == 1
        assert len(result.recommendations) == 1


@pytest.mark.skipif(not STATE_MANAGER_AVAILABLE, reason="State manager not available")
class TestTicketState:
    """Test ticket state data structure."""

    def test_ticket_state_creation(self):
        """Test creating ticket state."""
        state = TicketState(
            ticket_key="PROJ-123",
            content_hash="abc123",
            last_analyzed="2024-01-15T10:30:00Z"
        )
        
        assert state.ticket_key == "PROJ-123"
        assert state.content_hash == "abc123"
        assert state.metadata["version"] == "1.0"
        assert state.analysis_result is None

    def test_ticket_state_with_analysis(self):
        """Test ticket state with analysis result."""
        analysis = AnalysisResult(
            score=85.0,
            issues=[],
            recommendations=[],
            confidence=0.92,
            timestamp="2024-01-15T10:30:00Z"
        )
        
        state = TicketState(
            ticket_key="PROJ-123",
            content_hash="abc123",
            last_analyzed="2024-01-15T10:30:00Z",
            analysis_result=analysis
        )
        
        assert state.analysis_result is not None
        assert state.analysis_result.score == 85.0


@pytest.mark.skipif(not STATE_MANAGER_AVAILABLE, reason="State manager not available")
class TestPRState:
    """Test PR state data structure."""

    def test_pr_state_creation(self):
        """Test creating PR state."""
        state = PRState(
            pr_key="owner/repo#123",
            commit_sha="abc123",
            files_hash="def456",
            last_analyzed="2024-01-15T10:30:00Z"
        )
        
        assert state.pr_key == "owner/repo#123"
        assert state.commit_sha == "abc123"
        assert state.files_hash == "def456"
        assert state.metadata["version"] == "1.0"
        assert state.verification_result is None


@pytest.mark.skipif(not STATE_MANAGER_AVAILABLE, reason="State manager not available")
class TestStateManager:
    """Test state manager functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Create mock Redis client."""
        redis_mock = AsyncMock()
        return redis_mock

    @pytest.fixture
    def state_manager(self, mock_redis):
        """Create state manager with mock Redis."""
        return StateManager(redis_client=mock_redis)

    def test_make_key(self, state_manager):
        """Test Redis key generation."""
        key = state_manager._make_key(StateType.JIRA_TICKET, "PROJ-123")
        assert key == "pr_agent:state:jira:PROJ-123"
        
        key = state_manager._make_key(StateType.GITHUB_PR, "owner/repo#123")
        assert key == "pr_agent:state:github:owner/repo#123"

    @pytest.mark.asyncio
    async def test_get_ticket_state_not_found(self, state_manager, mock_redis):
        """Test getting non-existent ticket state."""
        mock_redis.get.return_value = None
        
        result = await state_manager.get_ticket_state("PROJ-123")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_ticket_state_redis_error(self, state_manager, mock_redis):
        """Test handling Redis errors gracefully."""
        mock_redis.get.side_effect = Exception("Redis error")
        
        result = await state_manager.get_ticket_state("PROJ-123")
        assert result is None

    @pytest.mark.asyncio
    async def test_set_ticket_state_success(self, state_manager, mock_redis):
        """Test setting ticket state successfully."""
        state = TicketState(
            ticket_key="PROJ-123",
            content_hash="abc123",
            last_analyzed="2024-01-15T10:30:00Z"
        )
        
        mock_redis.setex.return_value = True
        
        result = await state_manager.set_ticket_state(state)
        assert result is True
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_ticket_state_redis_error(self, state_manager, mock_redis):
        """Test handling Redis errors when setting state."""
        state = TicketState(
            ticket_key="PROJ-123",
            content_hash="abc123",
            last_analyzed="2024-01-15T10:30:00Z"
        )
        
        mock_redis.setex.side_effect = Exception("Redis error")
        
        result = await state_manager.set_ticket_state(state)
        assert result is False

    @pytest.mark.asyncio
    async def test_invalidate_state_success(self, state_manager, mock_redis):
        """Test invalidating state successfully."""
        mock_redis.delete.return_value = 1
        
        result = await state_manager.invalidate_state(StateType.JIRA_TICKET, "PROJ-123")
        assert result is True

    @pytest.mark.asyncio
    async def test_invalidate_state_not_found(self, state_manager, mock_redis):
        """Test invalidating non-existent state."""
        mock_redis.delete.return_value = 0
        
        result = await state_manager.invalidate_state(StateType.JIRA_TICKET, "PROJ-123")
        assert result is False


@pytest.mark.skipif(not STATE_MANAGER_AVAILABLE, reason="State manager not available")
class TestChangeDetector:
    """Test change detection functionality."""

    @pytest.fixture
    def mock_state_manager(self):
        """Create mock state manager."""
        return AsyncMock(spec=StateManager)

    @pytest.fixture
    def change_detector(self, mock_state_manager):
        """Create change detector with mock state manager."""
        return ChangeDetector(mock_state_manager)

    @pytest.mark.asyncio
    async def test_has_ticket_changed_no_cache(self, change_detector, mock_state_manager):
        """Test change detection when no cached state exists."""
        mock_state_manager.get_ticket_state.return_value = None
        
        result = await change_detector.has_ticket_changed("PROJ-123", "content", ["req1"])
        assert result is True

    @pytest.mark.asyncio
    async def test_has_ticket_changed_same_content(self, change_detector, mock_state_manager):
        """Test change detection with same content."""
        content = "test content"
        requirements = ["req1", "req2"]
        content_hash = ContentHasher.hash_dod_content(content, requirements)
        
        cached_state = TicketState(
            ticket_key="PROJ-123",
            content_hash=content_hash,
            last_analyzed="2024-01-15T10:30:00Z"
        )
        mock_state_manager.get_ticket_state.return_value = cached_state
        
        result = await change_detector.has_ticket_changed("PROJ-123", content, requirements)
        assert result is False

    @pytest.mark.asyncio
    async def test_has_ticket_changed_different_content(self, change_detector, mock_state_manager):
        """Test change detection with different content."""
        cached_state = TicketState(
            ticket_key="PROJ-123",
            content_hash="old_hash",
            last_analyzed="2024-01-15T10:30:00Z"
        )
        mock_state_manager.get_ticket_state.return_value = cached_state
        
        result = await change_detector.has_ticket_changed("PROJ-123", "new content", ["req1"])
        assert result is True

    @pytest.mark.asyncio
    async def test_should_reanalyze_force(self, change_detector, mock_state_manager):
        """Test that force flag always triggers reanalysis."""
        result = await change_detector.should_reanalyze(StateType.JIRA_TICKET, "PROJ-123", force=True)
        assert result is True

    @pytest.mark.asyncio
    async def test_should_reanalyze_no_cache(self, change_detector, mock_state_manager):
        """Test reanalysis when no cached state exists."""
        mock_state_manager.get_ticket_state.return_value = None
        
        result = await change_detector.should_reanalyze(StateType.JIRA_TICKET, "PROJ-123")
        assert result is True
