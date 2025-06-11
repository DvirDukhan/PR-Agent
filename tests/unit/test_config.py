"""Tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from pr_verification_agent.core.config import Config, JiraConfig, GitHubConfig, AIConfig


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
    
    def test_jira_config_missing_required(self):
        """Test Jira configuration with missing required fields."""
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
    
    def test_github_config_missing_required(self):
        """Test GitHub configuration with missing required fields."""
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
    
    def test_config_from_env_file(self, monkeypatch):
        """Test configuration loading from .env file."""
        # Create temporary .env file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("JIRA_SERVER_URL=https://test.atlassian.net\n")
            f.write("JIRA_EMAIL=test@example.com\n")
            f.write("JIRA_API_TOKEN=test-token\n")
            f.write("GITHUB_TOKEN=test-token\n")
            f.write("OPENAI_API_KEY=openai-key\n")
            env_file = f.name
        
        try:
            config = Config(env_file=env_file)
            assert config.jira.server_url == "https://test.atlassian.net"
            assert config.jira.email == "test@example.com"
            assert config.github.token == "test-token"
            assert config.ai.openai_api_key == "openai-key"
        finally:
            os.unlink(env_file)
