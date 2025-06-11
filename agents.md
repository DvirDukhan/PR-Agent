# AI Agent Guidelines for Repository-Aware GitHub PR Verification Project

## Project Mission
Create a repository-aware intelligent agent that operates from within the codebase, indexes the repository for context, and verifies GitHub pull requests against Jira issue Definition of Done (DoD) requirements. The agent ensures code changes align with business requirements while leveraging deep understanding of the existing codebase architecture and patterns.

## Agent Architecture

### Core Components
1. **Repository Indexing Agent**: Discovers, parses, and indexes codebase using Redis vector storage
2. **Context-Aware DoD Quality Assessor Agent**: Evaluates and improves Definition of Done quality with repository knowledge
3. **Repository-Aware PR Analysis Agent**: Analyzes pull request content against DoD requirements using codebase context
4. **Integration Orchestrator**: Coordinates between Jira, GitHub, Redis, and AI services
5. **User Interaction Agent**: Manages CLI conversations and feedback collection with repository status
6. **Codebase Search Agent**: Provides semantic search and similarity matching across the repository

## Agent Behavior Guidelines

### 1. Repository Indexing and Context Management

#### Indexing Strategy
- **File Discovery**: Recursively scan repository excluding .git, node_modules, build artifacts
- **Language Detection**: Identify programming languages and apply appropriate parsing
- **Code Chunking**: Split files into logical chunks (functions, classes, modules)
- **Vector Embedding**: Generate embeddings for code semantics and documentation
- **Incremental Updates**: Track file changes and update index efficiently
- **Metadata Storage**: Store file paths, timestamps, language, and structural information

#### Repository Context Awareness
- **Architecture Understanding**: Identify patterns, frameworks, and architectural decisions
- **Dependency Mapping**: Track imports, references, and module relationships
- **Code Style Analysis**: Learn project-specific coding patterns and conventions
- **Documentation Integration**: Index README files, comments, and inline documentation

### 2. Context-Aware Definition of Done Quality Assessment

#### Quality Criteria (Enhanced with Repository Context)
- **Detail Level**: DoD should contain sufficient technical implementation details aligned with codebase
- **Examples Provided**: Should include concrete examples relevant to the project's architecture
- **Technical Completeness**: Should cover functional and non-functional requirements feasible in current codebase
- **Specificity**: DoD should contain specific, actionable requirements matching project patterns
- **Measurability**: Criteria should be objectively verifiable within the repository context
- **Clarity**: Language should be unambiguous and clear using project terminology
- **Acceptance Criteria**: Should include clear pass/fail conditions testable in the codebase
- **Codebase Alignment**: Requirements should be technically feasible given existing architecture

#### Assessment Process (Repository-Enhanced)
1. Parse DoD text and extract key requirements
2. Search repository for similar implementations and patterns
3. Evaluate each criterion against quality standards and codebase feasibility
4. Cross-reference requirements with existing code architecture
5. Identify gaps, ambiguities, or technically infeasible elements
6. Generate specific improvement suggestions with code examples from repository
7. Engage user in interactive refinement process with repository context
8. Update Jira ticket with improved DoD including technical implementation notes

#### Interaction Patterns (Repository-Aware)
```
Agent: "I've analyzed the Definition of Done for JIRA-123 against your repository context. I found several areas that need clarification:

1. 'Feature should work properly' - This is too vague. Based on your existing test patterns in /tests/integration/,
   I suggest specifying: 'Feature should pass integration tests covering happy path, error cases, and edge cases
   following the pattern established in UserAuthenticationTest.java'

2. Missing acceptance criteria for error handling - I noticed your codebase uses a consistent error handling
   pattern with CustomException classes. The DoD should specify: 'All error scenarios should throw appropriate
   CustomException subclasses with meaningful error codes as seen in /src/exceptions/'

3. No mention of performance requirements - Your existing API endpoints have response time monitoring.
   Consider adding: 'API response time should be < 200ms as measured by existing PerformanceMonitor'

Would you like me to suggest specific improvements based on your repository's patterns?"
```

### 3. Repository-Aware Pull Request Analysis

#### Analysis Scope (Repository-Enhanced)
- **Code Changes**: Review modified files and their relationship to DoD requirements and existing patterns
- **Architectural Impact**: Analyze how changes fit within existing architecture and design patterns
- **Dependency Analysis**: Check if changes affect or require updates to related modules
- **Code Style Consistency**: Verify changes follow established project conventions
- **Commit Messages**: Analyze commit history for requirement traceability
- **Test Coverage**: Verify tests align with DoD acceptance criteria and existing test patterns
- **Documentation**: Check for required documentation updates consistent with project standards
- **Similar Code Patterns**: Compare implementation with existing similar functionality in the repository

#### Confidence Scoring
- **High (80-100%)**: All DoD requirements clearly addressed with evidence
- **Medium (50-79%)**: Most requirements addressed, minor gaps or unclear areas
- **Low (0-49%)**: Significant gaps or unclear requirement fulfillment

#### Analysis Output Format (Repository-Aware)
```
## PR Verification Results

**Confidence Level**: Medium (65%)
**Repository Context**: Analyzed against 1,247 indexed files across 15 modules

### Requirements Analysis
✅ **User Authentication**: Implemented OAuth2 integration as specified
   - Follows existing pattern in `src/auth/providers/GoogleAuthProvider.java`
   - Consistent with authentication interface defined in `src/auth/AuthProvider.java`

⚠️ **Error Handling**: Partial implementation, missing edge cases for network failures
   - Missing timeout handling pattern used in `src/network/HttpClient.java:89-102`
   - Should implement retry logic similar to `src/services/ExternalApiService.java:156-178`

❌ **Performance**: No evidence of load testing for 1000+ concurrent users
   - No performance tests found (existing pattern: `tests/performance/LoadTest.java`)
   - Missing connection pooling configuration (see `src/config/DatabaseConfig.java:45-67`)

### Repository Pattern Analysis
- **Similar Implementations**: Found 3 similar authentication flows in `/src/auth/providers/`
- **Code Reuse Opportunities**: Could leverage existing `TokenValidator` class
- **Architectural Consistency**: ✅ Follows established service layer pattern

### Improvement Suggestions
1. Add error handling for network timeout scenarios following pattern in `src/network/HttpClient.java:89-102`
2. Implement performance tests using existing framework in `tests/performance/LoadTestBase.java`
3. Update API documentation to reflect new authentication flow (follow format in `docs/api/authentication.md`)
4. Consider reusing `TokenValidator` from `src/auth/validation/TokenValidator.java`

### Files Reviewed
- `src/auth.py` (34 lines changed) - **New implementation**
- `tests/test_auth.py` (12 lines added) - **Missing performance tests**
- `docs/api.md` (5 lines modified) - **Needs consistency with existing docs**

### Related Repository Files
- `src/auth/providers/GoogleAuthProvider.java` - Similar pattern reference
- `src/network/HttpClient.java` - Error handling pattern
- `tests/performance/LoadTestBase.java` - Performance testing framework
```

### 4. RedisVL Vector Database Integration

#### RedisVL Architecture
- **SearchIndex**: Managed Redis search index with vector capabilities
- **Schema Definition**: Structured schema for codebase documents with metadata
- **Vectorizers**: Integrated sentence-transformers for embedding generation
- **Query System**: VectorQuery and FilterQuery for semantic and hybrid search

#### Storage Strategy (RedisVL)
- **Vector Embeddings**: Store code chunk embeddings using RedisVL SearchIndex
- **Metadata Fields**: Structured fields for file paths, language, functions, classes
- **Document Storage**: JSON/Hash storage with automatic validation
- **Index Management**: Automated index creation, updates, and optimization

#### Search and Retrieval (RedisVL)
- **Semantic Search**: VectorQuery with cosine similarity for code patterns
- **Filtered Search**: Combine vector similarity with metadata filters
- **Hybrid Queries**: Mix vector search with text and tag filtering
- **Result Ranking**: Distance-based scoring with similarity percentages

#### RedisVL Features Utilized
- **Automatic Vectorization**: Built-in sentence-transformers integration
- **Schema Validation**: Pydantic-based validation for document consistency
- **Async Support**: AsyncSearchIndex for high-performance operations
- **CLI Integration**: RedisVL CLI tools for index management and debugging
- **Performance Optimization**: HNSW algorithm for fast approximate search

### 5. User Interaction Principles

#### Communication Style
- **Conversational**: Use natural language, avoid technical jargon when possible
- **Specific**: Provide concrete examples and actionable feedback
- **Collaborative**: Frame suggestions as partnerships, not criticisms
- **Progressive**: Build understanding incrementally

#### Error Handling
- Gracefully handle API failures with clear user communication
- Provide fallback options when automated analysis fails
- Offer manual override capabilities for edge cases

### 4. Integration Best Practices

#### Jira Integration
- Use read-only access by default, request permission for updates
- Cache ticket data to minimize API calls
- Handle different Jira configurations (Server, Cloud, Data Center)
- Respect rate limits and implement exponential backoff

#### GitHub Integration
- Support both personal access tokens and GitHub Apps
- Handle large PRs efficiently (pagination, streaming)
- Respect GitHub API rate limits
- Support different repository configurations

#### AI Model Integration
- Implement model fallbacks for reliability
- Use structured prompts for consistent outputs
- Implement response validation and retry logic
- Monitor token usage and costs

### 5. Security and Privacy

#### Data Handling
- Never log sensitive information (API keys, personal data)
- Minimize data retention and implement cleanup
- Use secure credential storage
- Validate all inputs to prevent injection attacks

#### API Security
- Use least-privilege access principles
- Implement proper authentication for all services
- Validate SSL certificates and use secure connections
- Regular security audit of dependencies

### 6. Performance and Scalability

#### Optimization Strategies
- Implement caching for frequently accessed data
- Use async operations for I/O bound tasks
- Batch API requests when possible
- Implement request queuing for rate limit management

#### Monitoring
- Track API response times and error rates
- Monitor AI model performance and accuracy
- Log user satisfaction and feedback
- Implement health checks for all integrations

### 7. Testing Strategy

#### Unit Testing
- Mock all external API calls
- Test edge cases and error conditions
- Validate prompt engineering and response parsing
- Test configuration and credential handling

#### Integration Testing
- Test with real API endpoints in staging
- Validate end-to-end workflows
- Test different Jira and GitHub configurations
- Performance testing with large datasets

### 8. Continuous Improvement

#### Feedback Loop
- Collect user feedback on analysis accuracy
- Track false positives and negatives
- Monitor user satisfaction with DoD improvements
- Implement A/B testing for prompt variations

#### Model Training
- Collect anonymized examples of good/bad DoDs
- Track successful PR verifications
- Implement feedback mechanisms for model improvement
- Regular evaluation against benchmark datasets

## Implementation Notes

### CLI Design Principles
- **Interactive Chat Interface**: Conversational flow for natural user interaction
- **Progressive Disclosure**: Start simple, reveal complexity as needed
- **Clear Progress Indicators**: Visual feedback for long-running operations
- **Context Awareness**: Remember conversation state and user preferences
- **Helpful Prompts**: Guide users through complex workflows with suggestions

### Configuration Management
- Support multiple configuration sources (files, environment, CLI args)
- Validate configuration on startup
- Provide clear error messages for misconfigurations
- Support different environments (dev, staging, prod)

### Error Recovery
- Implement graceful degradation when services are unavailable
- Provide clear error messages with suggested solutions
- Support manual overrides for automated decisions
- Maintain operation logs for debugging

This document serves as the foundation for building an intelligent, reliable, and user-friendly PR verification agent that enhances development workflows while maintaining high standards for code quality and requirement compliance.
