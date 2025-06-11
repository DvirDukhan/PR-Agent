# GitHub Actions CI Setup

## Overview

This document describes the GitHub Actions CI/CD pipeline setup for the PR Verification Agent project.

## CI Workflow Features

### 🔧 **Multi-Python Version Testing**
- Tests against Python 3.9, 3.10, 3.11, and 3.12
- Ensures compatibility across different Python versions

### 🐳 **Redis Integration**
- Uses `redis:latest` Docker image
- Provides Redis server for basic functionality testing
- Includes health checks to ensure Redis is ready before tests

### 🧪 **Comprehensive Testing**
- **Unit Tests**: Configuration, vector store, and repository functionality
- **Integration Tests**: CLI commands and end-to-end workflows
- **Coverage Reporting**: Minimum 10% coverage requirement (will increase as project grows)

### 🔍 **Code Quality Checks**
- **Linting**: flake8 for syntax errors and code style
- **Formatting**: Black for consistent code formatting
- **Type Checking**: MyPy for static type analysis
- **Security Scanning**: Bandit for security vulnerabilities

### 📦 **Build and Package Testing**
- Package building with `python -m build`
- Package validation with `twine check`
- Artifact upload for distribution

## Workflow Structure

### 1. **Test Job**
```yaml
strategy:
  matrix:
    python-version: [3.9, 3.10, 3.11, 3.12]

services:
  redis:
    image: redis:latest
    ports:
      - 6379:6379
```

**Steps:**
- Checkout code
- Set up Python environment
- Cache pip dependencies
- Install dependencies from requirements.txt and requirements-dev.txt
- Wait for Redis to be ready
- Run linting (flake8)
- Run formatting check (black)
- Run type checking (mypy)
- Run tests with coverage
- Upload coverage to Codecov

### 2. **Integration Test Job**
**Dependencies:** Requires test job to pass

**Steps:**
- Test CLI installation and help
- Test configuration validation
- Test repository status (graceful failure handling)
- Test Git repository initialization
- Test repository indexing (with Redis)
- Test repository search functionality

### 3. **Security Job**
**Steps:**
- Run Bandit security scanner
- Upload security scan results as artifacts

### 4. **Build Job**
**Dependencies:** Requires test and integration-test jobs to pass

**Steps:**
- Build Python package
- Validate package with twine
- Upload build artifacts

## Environment Variables

The CI uses the following environment variables for testing:

```yaml
env:
  REDIS_URL: redis://localhost:6379
  REDIS_HOST: localhost
  REDIS_PORT: 6379
  JIRA_SERVER_URL: https://test.atlassian.net
  JIRA_EMAIL: test@example.com
  JIRA_API_TOKEN: test-token
  GITHUB_TOKEN: test-token
  OPENAI_API_KEY: test-key
  DEFAULT_AI_PROVIDER: openai
```

## Test Coverage

Current coverage target: **10%** (will be increased as more functionality is implemented)

Coverage includes:
- Configuration management (94% coverage)
- Core functionality testing
- CLI command validation
- Error handling verification

## Dependencies

### Core Dependencies
- `redisvl>=0.3.0` - Redis Vector Library for semantic search
- `sentence-transformers>=2.2.0` - Vector embeddings
- `click>=8.1.0` - CLI framework
- `rich>=13.0.0` - Rich terminal output
- `pydantic>=2.0.0` - Data validation
- `GitPython>=3.1.0` - Git repository operations

### Development Dependencies (requirements-dev.txt)
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async testing support
- `black>=23.0.0` - Code formatting
- `flake8>=6.0.0` - Linting
- `mypy>=1.5.0` - Type checking
- `bandit[toml]>=1.7.0` - Security scanning
- `build>=0.10.0` - Package building
- `twine>=4.0.0` - Package distribution

## Running Tests Locally

### Prerequisites
```bash
# Install Redis (basic Redis server)
docker run -d --name redis -p 6379:6379 redis:latest

# Or install locally
brew install redis  # macOS
```

### Setup
```bash
# Clone and setup
git clone <repository-url>
cd ai_week_project
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -e .
```

### Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pr_verification_agent

# Run specific test types
pytest tests/unit/
pytest tests/integration/

# Run linting
flake8 src/
black --check src/
mypy src/
```

## CI Status

The CI pipeline will:
- ✅ **Pass** when all tests pass, code is properly formatted, and coverage meets requirements
- ❌ **Fail** when tests fail, linting issues exist, or coverage is below threshold
- ⚠️ **Warn** for security issues (non-blocking) and missing optional dependencies

## Future Enhancements

1. **Increase Coverage**: Target 80%+ as more functionality is implemented
2. **Performance Testing**: Add benchmarks for repository indexing
3. **Docker Testing**: Test Docker containerization
4. **Release Automation**: Automatic PyPI publishing on tags
5. **Documentation**: Automated documentation generation and deployment

## Troubleshooting

### Common Issues

1. **Redis Connection Failures**
   - Ensure Redis Stack is running
   - Check port 6379 is available
   - Verify Redis health checks pass

2. **Import Errors**
   - Install all dependencies: `pip install -e .`
   - Check Python version compatibility

3. **Coverage Failures**
   - Run tests locally to debug coverage issues
   - Ensure all test files are included in coverage

4. **Linting Failures**
   - Run `black src/ tests/` to fix formatting
   - Run `flake8 src/` to identify issues

This CI setup ensures code quality, functionality, and compatibility across the development lifecycle.
