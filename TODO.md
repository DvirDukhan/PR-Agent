# GitHub PR Verification Agent - TODO

## Project Overview
Create a repository-aware AI agent that verifies GitHub pull requests against Jira issue Definition of Done (DoD) requirements. The agent runs from within the repository folder, indexes the codebase for context-aware analysis, and operates via CLI with future VSCode extension support.

## Phase 1: Foundation & Setup
- [x] Set up Python project structure
- [x] Create virtual environment and requirements.txt
- [x] Set up logging configuration
- [x] Create configuration management (API keys, endpoints)
- [x] Set up basic CLI framework (click)
- [x] Create project documentation structure
- [ ] Add Redis configuration and connection management
- [ ] Set up repository detection and validation
- [ ] Create codebase indexing framework

## Phase 2: Repository & Codebase Indexing (RedisVL)
- [x] Set up RedisVL integration and configuration
- [x] Create vector store implementation using RedisVL
- [x] Implement Git repository detection and validation
- [x] Create codebase file discovery and filtering
- [x] Implement basic code parsing and chunking strategies
- [x] Set up vector embedding generation using sentence-transformers
- [x] Create RedisVL schema for codebase indexing
- [x] Implement repository indexing with RedisVL SearchIndex
- [x] Add semantic search functionality using VectorQuery
- [x] Create CLI commands for indexing and search
- [ ] Implement incremental indexing (detect changes)
- [ ] Add advanced code parsing using tree-sitter
- [ ] Enhance metadata extraction (functions, classes, imports)
- [ ] Create unit tests for indexing functionality
- [ ] Add performance optimization for large repositories

## Phase 3: Jira Integration
- [ ] Install and configure Jira Python REST API library
- [ ] Implement Jira authentication (API token)
- [ ] Create Jira client wrapper class
- [ ] Implement ticket fetching functionality
- [ ] Implement ticket updating functionality (DoD improvements)
- [ ] Add error handling for Jira API calls
- [ ] Create unit tests for Jira integration

## Phase 4: GitHub Integration
- [ ] Evaluate GitHub API options (PyGithub vs requests + GitHub REST API)
- [ ] Implement GitHub authentication (personal access token)
- [ ] Create GitHub client wrapper class
- [ ] Implement PR fetching functionality (files, commits, comments)
- [ ] Implement PR commenting functionality
- [ ] Add error handling for GitHub API calls
- [ ] Create unit tests for GitHub integration

## Phase 5: AI Model Integration
- [ ] Implement dual AI provider support (OpenAI + Anthropic)
- [ ] Create configurable AI client with provider switching
- [ ] Create prompt templates for DoD quality assessment
- [ ] Create prompt templates for PR analysis with codebase context
- [ ] Implement confidence scoring logic
- [ ] Add retry logic and error handling for AI API calls
- [ ] Create unit tests for AI integration

## Phase 6: Context-Aware Definition of Done Analysis
- [ ] Define criteria for DoD quality assessment
  - [ ] Detail level and specificity
  - [ ] Examples provided in DoD
  - [ ] Technical implementation details
  - [ ] Acceptance criteria presence
  - [ ] Measurability and clarity
  - [ ] Codebase alignment and feasibility
- [ ] Implement DoD parsing and analysis with repository context
- [ ] Create interactive chat for DoD improvement
- [ ] Implement DoD update workflow
- [ ] Add validation for improved DoD against codebase
- [ ] Create unit tests for DoD analysis

## Phase 7: Repository-Aware Pull Request Analysis
- [ ] Implement PR content extraction (code changes, commit messages)
- [ ] Create codebase-aware analysis framework comparing PR to DoD
- [ ] Implement semantic code change analysis using vector search
- [ ] Cross-reference PR changes with existing codebase patterns
- [ ] Implement confidence scoring algorithm with context awareness
- [ ] Generate improvement suggestions based on repository knowledge
- [ ] Format analysis results for PR comments with code references
- [ ] Create unit tests for PR analysis

## Phase 8: Repository-Aware CLI Application
- [ ] Design interactive chat-based CLI interface with repository context
- [ ] Implement repository initialization and validation commands
- [ ] Implement conversational flow for DoD analysis with codebase awareness
- [ ] Implement conversational flow for PR verification with code context
- [ ] Add codebase indexing progress indicators and status
- [ ] Implement configuration file support for repository settings
- [ ] Add help documentation and examples for repository usage
- [ ] Create integration tests with sample repositories

## Phase 9: Testing & Quality Assurance
- [x] Set up pytest framework with Redis test containers
- [x] Create comprehensive unit tests for configuration
- [x] Add integration tests with CLI commands
- [x] Set up GitHub Actions CI with Redis Stack
- [x] Add code coverage reporting (10% minimum, targeting 80%)
- [x] Set up linting (flake8, black, mypy)
- [x] Add security scanning with bandit
- [x] Implement multi-Python version testing (3.9-3.12)
- [ ] Create comprehensive unit tests for vector store and repository
- [ ] Add end-to-end testing with sample repositories
- [ ] Implement performance benchmarks

## Phase 10: State Management & Anti-Spam System
- [ ] Design Redis-based state management for tickets and PRs
- [ ] Implement ticket state tracking (DoD content hash, analysis results)
- [ ] Implement PR state tracking (commit SHA, file changes hash, verification results)
- [ ] Create state comparison logic to detect meaningful changes
- [ ] Add caching layer for analysis results with TTL
- [ ] Implement smart response retrieval (return cached if unchanged)
- [ ] Add state invalidation triggers (manual refresh, time-based expiry)
- [ ] Create state management CLI commands (clear cache, view state)
- [ ] Add configuration for cache TTL and state retention policies
- [ ] Implement state migration and cleanup utilities

## Phase 11: Documentation
- [ ] Create comprehensive README.md with repository setup
- [ ] Add API documentation for indexing and search
- [ ] Create user guide and examples for repository usage
- [ ] Document configuration options including Redis
- [ ] Add troubleshooting guide for indexing issues

## Phase 12: VSCode Extension Development
- [ ] Research VSCode extension development and Language Server Protocol
- [ ] Design extension architecture with repository awareness
- [ ] Implement extension backend communication with CLI agent
- [ ] Create extension UI components for PR verification
- [ ] Implement real-time codebase indexing integration
- [ ] Add extension configuration and settings
- [ ] Package and distribute extension
- [ ] Create extension documentation and tutorials

## Technical Decisions to Make
- [ ] Choose between OpenAI and Anthropic (or support both)
- [ ] Select GitHub API approach (PyGithub vs REST API)
- [x] Select CLI framework for interactive chat (click + rich)
- [ ] Decide on configuration format (YAML, JSON, TOML)
- [ ] Choose testing framework and mocking strategy
- [x] Select logging framework and format (structlog + rich)
- [x] Choose vector database solution (RedisVL)
- [x] Choose vector embedding model for code indexing (sentence-transformers)
- [x] Select Redis configuration approach (RedisVL managed)
- [x] Decide on code chunking strategy for indexing (line-based with overlap)
- [x] Choose file type filtering for repository indexing (extension-based)
- [ ] Select tree-sitter languages for advanced parsing
- [ ] Choose incremental indexing strategy (hash-based change detection)

## Risk Mitigation
- [ ] Plan for API rate limiting
- [ ] Implement robust error handling
- [ ] Add input validation and sanitization
- [ ] Plan for large PR handling
- [ ] Consider security for API credentials
- [ ] Plan for different Jira/GitHub configurations
- [ ] Handle large repository indexing efficiently
- [ ] Implement Redis connection resilience
- [ ] Plan for repository access permissions
- [ ] Handle binary files and large files gracefully
- [ ] Implement incremental indexing to avoid full re-indexing
- [ ] Prevent spam with state management and caching (Phase 10)
- [ ] Handle duplicate analysis requests gracefully
- [ ] Implement cache invalidation strategies for data consistency

## Success Criteria
- [ ] Agent can assess DoD quality with 80%+ accuracy using repository context
- [ ] Agent can verify PR compliance with 75%+ accuracy with codebase awareness
- [ ] Repository indexing completes within reasonable time (< 5 min for typical repos)
- [ ] CLI is intuitive and user-friendly with clear repository status
- [ ] All integrations handle errors gracefully including Redis failures
- [ ] Code coverage > 80%
- [ ] Documentation is comprehensive and clear with repository setup examples
- [ ] VSCode extension provides seamless integration with repository workflow
