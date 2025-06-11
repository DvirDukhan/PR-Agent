# State Management & Anti-Spam System Design

## Overview

The PR Verification Agent needs intelligent state management to avoid spamming Jira tickets and GitHub PRs with duplicate analysis when nothing has changed. This system uses Redis to track the state of tickets and PRs, providing cached responses when content hasn't meaningfully changed.

## Problem Statement

### Current Issues
- **Spam Risk**: Multiple agent calls on unchanged tickets/PRs create noise
- **Resource Waste**: Re-analyzing identical content wastes API calls and compute
- **User Frustration**: Duplicate notifications and comments annoy users
- **Rate Limiting**: Unnecessary API calls may hit rate limits

### Requirements
- **Smart Caching**: Return cached results when content hasn't changed
- **Change Detection**: Identify meaningful changes that require re-analysis
- **Configurable TTL**: Allow time-based cache expiration
- **Manual Override**: Provide force refresh capability
- **State Visibility**: Allow users to inspect cached state

## Architecture Design

### Redis State Schema

#### Jira Ticket State
```json
{
  "ticket_key": "PROJ-123",
  "content_hash": "sha256_of_dod_content",
  "last_analyzed": "2024-01-15T10:30:00Z",
  "analysis_result": {
    "quality_score": 85,
    "issues": [...],
    "recommendations": [...],
    "confidence": 0.92
  },
  "metadata": {
    "version": "1.0",
    "analyzer_version": "0.1.0"
  }
}
```

#### GitHub PR State
```json
{
  "pr_key": "owner/repo#123",
  "commit_sha": "abc123...",
  "files_hash": "sha256_of_changed_files_content",
  "last_analyzed": "2024-01-15T10:30:00Z",
  "verification_result": {
    "compliance_score": 78,
    "violations": [...],
    "recommendations": [...],
    "confidence": 0.88
  },
  "metadata": {
    "version": "1.0",
    "analyzer_version": "0.1.0"
  }
}
```

### Redis Key Structure
```
pr_agent:state:jira:{ticket_key}
pr_agent:state:github:{owner}:{repo}:{pr_number}
pr_agent:config:cache_ttl
pr_agent:config:retention_policy
```

## Implementation Plan

### Phase 1: Core State Management

#### 1. State Storage Module
```python
class StateManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.default_ttl = 3600  # 1 hour
    
    async def get_ticket_state(self, ticket_key: str) -> Optional[TicketState]
    async def set_ticket_state(self, ticket_key: str, state: TicketState)
    async def get_pr_state(self, pr_key: str) -> Optional[PRState]
    async def set_pr_state(self, pr_key: str, state: PRState)
    async def invalidate_state(self, key: str)
    async def cleanup_expired_states()
```

#### 2. Content Hashing
```python
class ContentHasher:
    @staticmethod
    def hash_dod_content(dod_text: str, requirements: List[str]) -> str
    
    @staticmethod
    def hash_pr_content(files: List[FileChange], commits: List[Commit]) -> str
    
    @staticmethod
    def hash_repository_context(relevant_files: List[str]) -> str
```

#### 3. Change Detection
```python
class ChangeDetector:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
    
    async def has_ticket_changed(self, ticket_key: str, current_content: str) -> bool
    async def has_pr_changed(self, pr_key: str, current_sha: str, files: List[FileChange]) -> bool
    async def should_reanalyze(self, key: str, force: bool = False) -> bool
```

### Phase 2: Smart Response System

#### 1. Analysis Cache
```python
class AnalysisCache:
    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
    
    async def get_cached_analysis(self, key: str) -> Optional[AnalysisResult]
    async def cache_analysis(self, key: str, result: AnalysisResult, ttl: int = None)
    async def invalidate_analysis(self, key: str)
```

#### 2. Smart Agent Wrapper
```python
class SmartVerificationAgent:
    def __init__(self, base_agent: VerificationAgent, cache: AnalysisCache):
        self.agent = base_agent
        self.cache = cache
    
    async def analyze_dod(self, ticket_key: str, force: bool = False) -> AnalysisResult:
        # Check cache first, analyze only if changed
        
    async def verify_pr(self, pr_key: str, force: bool = False) -> VerificationResult:
        # Check cache first, verify only if changed
```

### Phase 3: Configuration & Management

#### 1. Cache Configuration
```yaml
# config.yml
cache:
  default_ttl: 3600  # 1 hour
  max_ttl: 86400     # 24 hours
  retention_days: 30
  cleanup_interval: 3600
  
state_management:
  enable_caching: true
  force_refresh_threshold: 7200  # 2 hours
  hash_algorithm: "sha256"
```

#### 2. CLI Commands
```bash
# View cached state
pr-agent state show --ticket PROJ-123
pr-agent state show --pr owner/repo#123

# Clear cache
pr-agent state clear --ticket PROJ-123
pr-agent state clear --pr owner/repo#123
pr-agent state clear --all

# Force refresh
pr-agent analyze --ticket PROJ-123 --force
pr-agent verify --pr owner/repo#123 --force

# Cache statistics
pr-agent state stats
```

## Change Detection Logic

### Jira Ticket Changes
- **DoD Content**: Hash of description, acceptance criteria, requirements
- **Ticket Updates**: Last modified timestamp comparison
- **Related Issues**: Changes in linked tickets or dependencies

### GitHub PR Changes
- **Commit SHA**: New commits pushed to the branch
- **File Changes**: Modified files, added/removed files
- **PR Metadata**: Title, description, labels, reviewers

### Repository Context Changes
- **Relevant Files**: Changes in files that provide context for analysis
- **Dependencies**: Updates to package files, configuration changes
- **Architecture**: Structural changes that affect analysis context

## Anti-Spam Features

### 1. Intelligent Notifications
- **Suppress Duplicates**: Don't notify if analysis result is identical
- **Threshold Changes**: Only notify if confidence or score changes significantly
- **Batch Updates**: Combine multiple small changes into single notification

### 2. Rate Limiting
- **Per-Ticket Limits**: Maximum analysis frequency per ticket
- **Per-User Limits**: Prevent individual users from spamming
- **Global Limits**: System-wide rate limiting

### 3. Smart Responses
- **Cached Response Format**: Clearly indicate when returning cached results
- **Change Summary**: Show what changed since last analysis
- **Freshness Indicator**: Display age of cached analysis

## Example Usage

### Scenario 1: Unchanged Ticket
```python
# First call - performs full analysis
result1 = await agent.analyze_dod("PROJ-123")
# Returns: Fresh analysis with confidence 0.92

# Second call 10 minutes later - returns cached result
result2 = await agent.analyze_dod("PROJ-123")
# Returns: Cached analysis (age: 10m) with confidence 0.92
```

### Scenario 2: Updated PR
```python
# Initial PR analysis
result1 = await agent.verify_pr("owner/repo#123")
# Analyzes commit abc123, caches result

# New commit pushed
result2 = await agent.verify_pr("owner/repo#123")
# Detects new commit def456, performs fresh analysis
```

### Scenario 3: Force Refresh
```python
# Force fresh analysis despite cache
result = await agent.analyze_dod("PROJ-123", force=True)
# Bypasses cache, performs new analysis, updates cache
```

## Benefits

### For Users
- **Reduced Noise**: No duplicate notifications or comments
- **Faster Responses**: Cached results return immediately
- **Clear Indicators**: Know when results are fresh vs cached

### For System
- **Resource Efficiency**: Avoid redundant API calls and compute
- **Rate Limit Protection**: Reduce risk of hitting API limits
- **Scalability**: Handle more users with same resources

### For Development
- **Debugging**: Clear state visibility for troubleshooting
- **Testing**: Predictable behavior with state management
- **Monitoring**: Track cache hit rates and performance

## Implementation Priority

1. **High Priority**: Core state storage and change detection
2. **Medium Priority**: Smart response system and CLI commands
3. **Low Priority**: Advanced features like batch notifications

This state management system will make the PR Verification Agent production-ready by eliminating spam while maintaining responsiveness and accuracy.
