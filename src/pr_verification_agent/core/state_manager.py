"""State management for preventing spam and caching analysis results."""

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

import redis.asyncio as redis

from .config import config
from .logging import get_logger

logger = get_logger(__name__)


class StateType(Enum):
    """Types of state that can be managed."""
    JIRA_TICKET = "jira"
    GITHUB_PR = "github"


@dataclass
class AnalysisResult:
    """Generic analysis result structure."""
    score: float
    issues: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence: float
    timestamp: str
    analyzer_version: str = "0.1.0"


@dataclass
class TicketState:
    """State tracking for Jira tickets."""
    ticket_key: str
    content_hash: str
    last_analyzed: str
    analysis_result: Optional[AnalysisResult] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {"version": "1.0"}


@dataclass
class PRState:
    """State tracking for GitHub PRs."""
    pr_key: str
    commit_sha: str
    files_hash: str
    last_analyzed: str
    verification_result: Optional[AnalysisResult] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {"version": "1.0"}


class ContentHasher:
    """Utility for creating content hashes."""

    @staticmethod
    def hash_content(content: Union[str, List[str], Dict[str, Any]]) -> str:
        """Create SHA256 hash of content."""
        if isinstance(content, str):
            data = content.encode('utf-8')
        elif isinstance(content, (list, dict)):
            data = json.dumps(content, sort_keys=True).encode('utf-8')
        else:
            data = str(content).encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_dod_content(dod_text: str, requirements: List[str]) -> str:
        """Hash DoD content for change detection."""
        combined_content = {
            "dod_text": dod_text,
            "requirements": sorted(requirements)
        }
        return ContentHasher.hash_content(combined_content)

    @staticmethod
    def hash_pr_content(files: List[Dict[str, Any]], commits: List[str]) -> str:
        """Hash PR content for change detection."""
        combined_content = {
            "files": sorted([f.get("filename", "") for f in files]),
            "commits": sorted(commits)
        }
        return ContentHasher.hash_content(combined_content)


class StateManager:
    """Redis-based state management for caching and spam prevention."""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize state manager.
        
        Args:
            redis_client: Optional Redis client, will create one if not provided
        """
        self.redis = redis_client
        self.default_ttl = config.cache.get("default_ttl", 3600)  # 1 hour
        self.key_prefix = "pr_agent:state"

    async def _ensure_redis(self) -> redis.Redis:
        """Ensure Redis client is available."""
        if self.redis is None:
            self.redis = redis.from_url(config.redis.connection_url)
        return self.redis

    def _make_key(self, state_type: StateType, identifier: str) -> str:
        """Create Redis key for state storage."""
        return f"{self.key_prefix}:{state_type.value}:{identifier}"

    async def get_ticket_state(self, ticket_key: str) -> Optional[TicketState]:
        """Get cached ticket state."""
        try:
            redis_client = await self._ensure_redis()
            key = self._make_key(StateType.JIRA_TICKET, ticket_key)
            
            data = await redis_client.get(key)
            if data is None:
                return None
            
            state_dict = json.loads(data)
            
            # Convert analysis_result back to AnalysisResult if present
            if state_dict.get("analysis_result"):
                state_dict["analysis_result"] = AnalysisResult(**state_dict["analysis_result"])
            
            return TicketState(**state_dict)
            
        except Exception as e:
            logger.warning(f"Failed to get ticket state for {ticket_key}: {e}")
            return None

    async def set_ticket_state(self, state: TicketState, ttl: Optional[int] = None) -> bool:
        """Set ticket state in cache."""
        try:
            redis_client = await self._ensure_redis()
            key = self._make_key(StateType.JIRA_TICKET, state.ticket_key)
            
            # Convert to dict for JSON serialization
            state_dict = asdict(state)
            data = json.dumps(state_dict, default=str)
            
            ttl = ttl or self.default_ttl
            await redis_client.setex(key, ttl, data)
            
            logger.debug(f"Cached ticket state for {state.ticket_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set ticket state for {state.ticket_key}: {e}")
            return False

    async def get_pr_state(self, pr_key: str) -> Optional[PRState]:
        """Get cached PR state."""
        try:
            redis_client = await self._ensure_redis()
            key = self._make_key(StateType.GITHUB_PR, pr_key)
            
            data = await redis_client.get(key)
            if data is None:
                return None
            
            state_dict = json.loads(data)
            
            # Convert verification_result back to AnalysisResult if present
            if state_dict.get("verification_result"):
                state_dict["verification_result"] = AnalysisResult(**state_dict["verification_result"])
            
            return PRState(**state_dict)
            
        except Exception as e:
            logger.warning(f"Failed to get PR state for {pr_key}: {e}")
            return None

    async def set_pr_state(self, state: PRState, ttl: Optional[int] = None) -> bool:
        """Set PR state in cache."""
        try:
            redis_client = await self._ensure_redis()
            key = self._make_key(StateType.GITHUB_PR, state.pr_key)
            
            # Convert to dict for JSON serialization
            state_dict = asdict(state)
            data = json.dumps(state_dict, default=str)
            
            ttl = ttl or self.default_ttl
            await redis_client.setex(key, ttl, data)
            
            logger.debug(f"Cached PR state for {state.pr_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set PR state for {state.pr_key}: {e}")
            return False

    async def invalidate_state(self, state_type: StateType, identifier: str) -> bool:
        """Invalidate cached state."""
        try:
            redis_client = await self._ensure_redis()
            key = self._make_key(state_type, identifier)
            
            result = await redis_client.delete(key)
            logger.debug(f"Invalidated state for {state_type.value}:{identifier}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to invalidate state for {state_type.value}:{identifier}: {e}")
            return False

    async def cleanup_expired_states(self) -> int:
        """Clean up expired states (Redis handles this automatically with TTL)."""
        # Redis automatically handles TTL expiration
        # This method is for manual cleanup if needed
        try:
            redis_client = await self._ensure_redis()
            pattern = f"{self.key_prefix}:*"
            
            # Get all keys matching pattern
            keys = await redis_client.keys(pattern)
            
            # Check TTL for each key and count expired ones
            expired_count = 0
            for key in keys:
                ttl = await redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1
            
            logger.info(f"Found {expired_count} expired state entries")
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired states: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            redis_client = await self._ensure_redis()
            pattern = f"{self.key_prefix}:*"
            
            keys = await redis_client.keys(pattern)
            
            stats = {
                "total_keys": len(keys),
                "jira_tickets": 0,
                "github_prs": 0,
                "expired_keys": 0
            }
            
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                if ":jira:" in key_str:
                    stats["jira_tickets"] += 1
                elif ":github:" in key_str:
                    stats["github_prs"] += 1
                
                # Check if expired
                ttl = await redis_client.ttl(key)
                if ttl == -2:
                    stats["expired_keys"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}


class ChangeDetector:
    """Detect meaningful changes in tickets and PRs."""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager

    async def has_ticket_changed(self, ticket_key: str, current_content: str, 
                               requirements: List[str]) -> bool:
        """Check if ticket content has changed significantly."""
        try:
            cached_state = await self.state_manager.get_ticket_state(ticket_key)
            if cached_state is None:
                return True  # No cached state, consider it changed
            
            current_hash = ContentHasher.hash_dod_content(current_content, requirements)
            return current_hash != cached_state.content_hash
            
        except Exception as e:
            logger.warning(f"Error checking ticket changes for {ticket_key}: {e}")
            return True  # Assume changed on error

    async def has_pr_changed(self, pr_key: str, current_sha: str, 
                           files: List[Dict[str, Any]]) -> bool:
        """Check if PR content has changed significantly."""
        try:
            cached_state = await self.state_manager.get_pr_state(pr_key)
            if cached_state is None:
                return True  # No cached state, consider it changed
            
            # Check commit SHA first (most common change)
            if current_sha != cached_state.commit_sha:
                return True
            
            # Check file changes
            current_files_hash = ContentHasher.hash_pr_content(files, [current_sha])
            return current_files_hash != cached_state.files_hash
            
        except Exception as e:
            logger.warning(f"Error checking PR changes for {pr_key}: {e}")
            return True  # Assume changed on error

    async def should_reanalyze(self, state_type: StateType, identifier: str, 
                             force: bool = False) -> bool:
        """Determine if reanalysis is needed."""
        if force:
            return True
        
        try:
            if state_type == StateType.JIRA_TICKET:
                state = await self.state_manager.get_ticket_state(identifier)
            else:
                state = await self.state_manager.get_pr_state(identifier)
            
            if state is None:
                return True  # No cached state
            
            # Check if analysis is too old (configurable threshold)
            force_refresh_threshold = config.cache.get("force_refresh_threshold", 7200)  # 2 hours
            
            last_analyzed = datetime.fromisoformat(state.last_analyzed.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age_seconds = (now - last_analyzed).total_seconds()
            
            if age_seconds > force_refresh_threshold:
                logger.info(f"Analysis for {identifier} is {age_seconds}s old, forcing refresh")
                return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking reanalysis need for {identifier}: {e}")
            return True  # Assume reanalysis needed on error
