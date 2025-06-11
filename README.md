# PR Verification Agent 🤖

A repository-aware intelligent AI agent that operates from within your codebase, indexes your repository for deep context understanding, and verifies GitHub pull requests against Jira Definition of Done (DoD) requirements. The agent ensures code changes align with business requirements while leveraging comprehensive knowledge of your existing codebase architecture and patterns.

## 🎯 Project Goals

1. **Repository-Aware AI Agent**: Build a state-of-the-art AI agent that understands your codebase architecture and patterns
2. **Codebase Indexing**: Index repository content using Redis vector database for semantic code search and analysis
3. **Context-Aware DoD Validation**: Cross-validate Definition of Done quality with repository feasibility and architectural alignment
4. **Intelligent PR Verification**: Analyze pull requests against DoD requirements using deep codebase context and existing patterns
5. **CLI to VSCode Progression**: Start as a Python CLI application, evolve into a VSCode extension for seamless IDE integration

## 🚀 Features

- **RedisVL-Powered Indexing**: Automatically discovers and indexes your codebase using RedisVL vector database
- **Advanced Semantic Search**: Find similar code patterns, functions, and architectural decisions with vector similarity
- **Context-Aware DoD Analysis**: Evaluates Definition of Done quality with repository feasibility and architectural alignment
- **Interactive Chat Interface**: Conversational CLI with repository context and codebase awareness
- **Intelligent PR Verification**: Analyzes code changes against DoD requirements using existing codebase patterns
- **Confidence Scoring**: Provides Low/Medium/High confidence levels based on repository context and pattern matching
- **Multi-Provider AI Support**: Configurable support for OpenAI and Anthropic models with codebase-aware prompts
- **Comprehensive Integrations**: Seamless Jira, GitHub, and RedisVL integration
- **Repository-Aware Suggestions**: Actionable feedback referencing existing code patterns and architectural decisions
- **High-Performance Search**: HNSW algorithm for fast approximate vector search across large codebases

## 📋 Current Status

This project is in **Phase 1: Foundation & Setup**. The basic project structure, configuration management, and CLI framework are implemented.

### ✅ Completed
- [x] Project structure and packaging setup
- [x] Configuration management with environment variables
- [x] Logging configuration with structured logging
- [x] Basic CLI framework with Rich UI
- [x] Development environment setup

### 🚧 In Progress
- [ ] Jira integration implementation
- [ ] GitHub integration implementation
- [ ] AI model integration
- [ ] DoD analysis agents
- [ ] PR verification agents

## 🛠️ Installation

### Prerequisites
- Python 3.9 or higher
- Git
- Redis server (for vector database)
- Access to a Git repository for indexing

### Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd ai_week_project
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start Redis Stack server** (required for RedisVL):
   ```bash
   # Using Docker (recommended) - includes Redis with Search & Query
   docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest

   # This also provides Redis Insight GUI at http://localhost:8001

   # Or install Redis Stack locally
   # macOS: brew install redis-stack
   # Ubuntu: Follow Redis Stack installation guide
   ```

5. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys, Redis connection, and repository settings
   ```

6. **Install in development mode**:
   ```bash
   pip install -e .
   ```

7. **Initialize repository indexing** (run from your target repository):
   ```bash
   cd /path/to/your/repository
   pr-agent index --initialize
   ```

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure the following:

### Jira Configuration
```env
JIRA_SERVER_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-jira-api-token
```

### GitHub Configuration
```env
GITHUB_TOKEN=your-github-personal-access-token
```

### AI Model Configuration
```env
# Choose one or both providers
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
DEFAULT_AI_PROVIDER=openai  # or anthropic
```

### Redis Configuration
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional
REDIS_DB=0
```

### Repository Indexing Configuration
```env
REPO_EMBEDDING_MODEL=all-MiniLM-L6-v2
REPO_CHUNK_SIZE=512
REPO_MAX_FILE_SIZE_MB=10
REPO_EXCLUDED_DIRS=.git,node_modules,__pycache__,build,dist
REPO_INCLUDED_EXTENSIONS=.py,.js,.ts,.java,.cpp,.c,.h,.cs,.go,.rs
```

## 🖥️ Usage

**Important**: Run all commands from within your target repository directory for full context awareness.

### Initialize Repository Indexing
```bash
cd /path/to/your/repository
pr-agent index --initialize
```

### Update Repository Index
```bash
pr-agent index --update
```

### Interactive Chat Mode (Repository-Aware)
```bash
pr-agent chat
```

### Analyze Definition of Done (with Repository Context)
```bash
pr-agent analyze-dod PROJ-123
```

### Verify Pull Request (with Codebase Analysis)
```bash
pr-agent verify-pr https://github.com/owner/repo/pull/123 --jira-ticket PROJ-123
```

### Search Repository
```bash
pr-agent search "authentication implementation"
pr-agent search --semantic "error handling patterns"
```

### Repository Status
```bash
pr-agent status
```

### Check Configuration
```bash
pr-agent config-check
```

## 🏗️ Architecture

```
src/pr_verification_agent/
├── core/           # Core functionality
│   ├── config.py   # Configuration management
│   └── logging.py  # Logging setup
├── integrations/   # External service integrations
│   ├── jira.py     # Jira API client
│   ├── github.py   # GitHub API client
│   └── ai.py       # AI model providers
├── agents/         # AI agent implementations
│   ├── dod_agent.py    # Definition of Done analysis
│   ├── pr_agent.py     # Pull request verification
│   └── chat_agent.py   # Interactive chat interface
├── utils/          # Utility functions
└── cli.py          # Command-line interface
```

## 🧪 Development

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/pr_verification_agent

# Run specific test types
pytest tests/unit/
pytest tests/integration/
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## 📚 Documentation

- [TODO.md](TODO.md) - Detailed project roadmap and task breakdown
- [agents.md](agents.md) - AI agent guidelines and behavior specifications
- [docs/](docs/) - Additional documentation (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔮 Future Plans

- **VSCode Extension**: Transform the CLI into a VSCode extension for seamless IDE integration
- **Advanced AI Models**: Support for additional AI providers and models
- **Custom DoD Templates**: Predefined templates for common project types
- **Team Analytics**: Insights and metrics on DoD quality and PR compliance
- **Webhook Integration**: Automated PR verification on GitHub events

## 📞 Support

For questions, issues, or contributions, please:
- Open an issue on GitHub
- Check the [TODO.md](TODO.md) for current development status
- Review [agents.md](agents.md) for AI agent specifications

---

**Built with ❤️ for better software development workflows**
