"""Tests for configuration management."""

import pytest

from pr_verification_agent.core.config import (
    Config,
    JiraConfig,
    GitHubConfig,
    AIConfig,
    RedisConfig,
    RepositoryConfig,
)


class TestJiraConfig:
    """Test Jira configuration."""

    def test_jira_config_valid(self, monkeypatch):
        """Test valid Jira configuration."""
        monkeypatch.setenv("JIRA_SERVER_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")

        config = JiraConfig()
        assert config.server_url == "https://test.atlassian.net"
        assert config.email == "test@example.com"
        assert config.api_token == "test-token"

    def test_jira_config_missing_optional(self):
        """Test Jira configuration with missing optional fields."""
        # Since fields are now optional, this should not raise
        config = JiraConfig()
        assert config.server_url is None
        assert config.email is None
        assert config.api_token is None


class TestGitHubConfig:
    """Test GitHub configuration."""

    def test_github_config_valid(self, monkeypatch):
        """Test valid GitHub configuration."""
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")

        config = GitHubConfig()
        assert config.token == "test-token"

    def test_github_config_missing_optional(self):
        """Test GitHub configuration with missing optional fields."""
        # Since fields are now optional, this should not raise
        config = GitHubConfig()
        assert config.token is None


class TestAIConfig:
    """Test AI configuration."""

    def test_ai_config_defaults(self):
        """Test AI configuration with defaults."""
        config = AIConfig()
        assert config.openai_api_key is None
        assert config.anthropic_api_key is None
        assert config.default_provider == "openai"

    def test_ai_config_with_keys(self, monkeypatch):
        """Test AI configuration with API keys."""
        # Clear any existing env vars first
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("DEFAULT_AI_PROVIDER", raising=False)

        # Set new values
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")
        monkeypatch.setenv("DEFAULT_AI_PROVIDER", "anthropic")

        config = AIConfig()
        assert config.openai_api_key == "openai-key"
        assert config.anthropic_api_key == "anthropic-key"
        assert config.default_provider == "anthropic"


class TestRedisConfig:
    """Test Redis configuration."""

    def test_redis_config_defaults(self):
        """Test Redis configuration with defaults."""
        config = RedisConfig()
        assert config.url == "redis://localhost:6379"
        assert config.host == "localhost"
        assert config.port == 6379
        assert config.password is None
        assert config.db == 0

    def test_redis_config_connection_url_default(self):
        """Test Redis connection URL generation with defaults."""
        config = RedisConfig()
        assert config.connection_url == "redis://localhost:6379/0"

    def test_redis_config_connection_url_with_password(self, monkeypatch):
        """Test Redis connection URL generation with password."""
        monkeypatch.delenv("REDIS_URL", raising=False)
        monkeypatch.setenv("REDIS_PASSWORD", "secret")

        config = RedisConfig()
        assert config.connection_url == "redis://:secret@localhost:6379/0"

    def test_redis_config_custom_url(self, monkeypatch):
        """Test Redis configuration with custom URL."""
        monkeypatch.setenv("REDIS_URL", "redis://custom:6380/1")

        config = RedisConfig()
        assert config.connection_url == "redis://custom:6380/1"


class TestRepositoryConfig:
    """Test Repository configuration."""

    def test_repository_config_defaults(self):
        """Test Repository configuration with defaults."""
        config = RepositoryConfig()
        assert config.index_name == "pr_agent_codebase"
        assert config.index_prefix == "codebase_docs"
        assert config.vectorizer == "sentence-transformers"
        assert config.embedding_model == "all-MiniLM-L6-v2"
        assert config.vector_dims == 384
        assert config.distance_metric == "cosine"
        assert config.chunk_size == 512

    def test_repository_config_excluded_dirs_list(self):
        """Test excluded directories list property."""
        config = RepositoryConfig()
        excluded = config.excluded_dirs_list
        assert ".git" in excluded
        assert "node_modules" in excluded
        assert "__pycache__" in excluded

    def test_repository_config_included_extensions_list(self):
        """Test included extensions list property."""
        config = RepositoryConfig()
        extensions = config.included_extensions_list
        assert ".py" in extensions
        assert ".js" in extensions
        assert ".java" in extensions


class TestConfig:
    """Test main configuration class."""

    def test_config_validation_openai_missing_key(self, monkeypatch):
        """Test configuration validation with missing OpenAI key."""
        # Set required fields
        monkeypatch.setenv("JIRA_SERVER_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("DEFAULT_AI_PROVIDER", "openai")
        # Don't set OPENAI_API_KEY

        config = Config()
        with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
            config.validate()

    def test_config_validation_anthropic_missing_key(self, monkeypatch):
        """Test configuration validation with missing Anthropic key."""
        # Set required fields
        monkeypatch.setenv("JIRA_SERVER_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("DEFAULT_AI_PROVIDER", "anthropic")
        # Don't set ANTHROPIC_API_KEY

        config = Config()
        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY is required"):
            config.validate()

    def test_config_validation_invalid_provider(self, monkeypatch):
        """Test configuration validation with invalid AI provider."""
        # Set required fields
        monkeypatch.setenv("JIRA_SERVER_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("DEFAULT_AI_PROVIDER", "invalid")

        config = Config()
        with pytest.raises(ValueError, match="Invalid AI provider"):
            config.validate()

    def test_config_validation_success(self, monkeypatch):
        """Test successful configuration validation."""
        # Set all required fields
        monkeypatch.setenv("JIRA_SERVER_URL", "https://test.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "test-token")
        monkeypatch.setenv("GITHUB_TOKEN", "test-token")
        monkeypatch.setenv("DEFAULT_AI_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

        config = Config()
        config.validate()  # Should not raise

    def test_config_includes_all_sections(self):
        """Test that config includes all configuration sections."""
        config = Config()
        assert hasattr(config, "jira")
        assert hasattr(config, "github")
        assert hasattr(config, "ai")
        assert hasattr(config, "redis")
        assert hasattr(config, "repository")
        assert hasattr(config, "app")
