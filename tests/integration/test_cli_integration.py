"""Integration tests for CLI functionality."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLIIntegration:
    """Test CLI integration functionality."""

    def test_cli_help(self):
        """Test that CLI help command works."""
        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "PR Verification Agent" in result.stdout
        assert "chat" in result.stdout
        assert "index" in result.stdout
        assert "search" in result.stdout
        assert "status" in result.stdout

    def test_cli_version(self):
        """Test that CLI version command works."""
        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "--version"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_config_check_missing_config(self):
        """Test config check with missing configuration."""
        # Run without environment variables
        env = os.environ.copy()
        # Remove any existing config
        for key in list(env.keys()):
            if key.startswith(("JIRA_", "GITHUB_", "OPENAI_", "ANTHROPIC_", "REDIS_")):
                del env[key]

        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "config-check"],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should fail due to missing configuration
        assert result.returncode != 0
        assert "Configuration validation failed" in result.stderr

    def test_config_check_with_config(self):
        """Test config check with valid configuration."""
        env = os.environ.copy()
        env.update(
            {
                "JIRA_SERVER_URL": "https://test.atlassian.net",
                "JIRA_EMAIL": "test@example.com",
                "JIRA_API_TOKEN": "test-token",
                "GITHUB_TOKEN": "test-token",
                "OPENAI_API_KEY": "test-key",
                "DEFAULT_AI_PROVIDER": "openai",
                "REDIS_URL": "redis://localhost:6379",
            }
        )

        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "config-check"],
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0
        assert "Repository Configuration" in result.stdout
        assert "Redis Configuration" in result.stdout
        assert "Jira Configuration" in result.stdout

    @pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="Redis not available")
    def test_status_command(self):
        """Test status command with Redis available."""
        env = os.environ.copy()
        env.update({"REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379")})

        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "status"],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should work even without a Git repository
        assert "Repository Status" in result.stdout

    def test_index_command_no_git_repo(self):
        """Test index command outside of Git repository."""
        with tempfile.TemporaryDirectory() as temp_dir:
            env = os.environ.copy()
            env.update({"REDIS_URL": "redis://localhost:6379"})

            result = subprocess.run(
                ["python", "-m", "pr_verification_agent.cli", "index", "--initialize"],
                capture_output=True,
                text=True,
                cwd=temp_dir,
                env=env,
            )

            # Should fail gracefully with no Git repository
            assert (
                "Repository validation failed" in result.stdout
                or result.returncode != 0
            )

    @pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="Redis not available")
    def test_search_command_no_index(self):
        """Test search command with no index."""
        env = os.environ.copy()
        env.update({"REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379")})

        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "search", "test query"],
            capture_output=True,
            text=True,
            env=env,
        )

        # Should handle missing index gracefully
        assert "Search failed" in result.stdout or "No results found" in result.stdout


class TestCLIWithGitRepo:
    """Test CLI functionality with a Git repository."""

    @pytest.fixture
    def git_repo(self):
        """Create a temporary Git repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)

            # Initialize Git repository
            subprocess.run(["git", "init"], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_path,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=repo_path, check=True
            )

            # Create some test files
            (repo_path / "README.md").write_text("# Test Repository\n\nThis is a test.")
            (repo_path / "main.py").write_text(
                """
def hello_world():
    print("Hello, World!")

def calculate_sum(a, b):
    return a + b

if __name__ == "__main__":
    hello_world()
    result = calculate_sum(5, 3)
    print(f"Sum: {result}")
"""
            )
            (repo_path / "utils.py").write_text(
                """
import os
import sys

class FileHelper:
    def __init__(self, base_path):
        self.base_path = base_path
    
    def read_file(self, filename):
        with open(os.path.join(self.base_path, filename), 'r') as f:
            return f.read()
"""
            )

            # Add and commit files
            subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True
            )

            yield repo_path

    def test_status_in_git_repo(self, git_repo):
        """Test status command in a Git repository."""
        env = os.environ.copy()
        env.update({"REDIS_URL": "redis://localhost:6379"})

        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "status"],
            capture_output=True,
            text=True,
            cwd=git_repo,
            env=env,
        )

        assert "Repository Status" in result.stdout
        assert str(git_repo) in result.stdout or "Repository:" in result.stdout

    @pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="Redis not available")
    def test_index_initialize_in_git_repo(self, git_repo):
        """Test index initialization in a Git repository."""
        env = os.environ.copy()
        env.update({"REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379")})

        result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "index", "--initialize"],
            capture_output=True,
            text=True,
            cwd=git_repo,
            env=env,
            timeout=60,  # Give it time to download models if needed
        )

        # Check if indexing was attempted
        assert "Starting repository indexing" in result.stdout or result.returncode == 0

    @pytest.mark.skipif(not os.environ.get("REDIS_URL"), reason="Redis not available")
    def test_search_after_index(self, git_repo):
        """Test search after indexing (if indexing succeeds)."""
        env = os.environ.copy()
        env.update({"REDIS_URL": os.environ.get("REDIS_URL", "redis://localhost:6379")})

        # Try to initialize index first
        index_result = subprocess.run(
            ["python", "-m", "pr_verification_agent.cli", "index", "--initialize"],
            capture_output=True,
            text=True,
            cwd=git_repo,
            env=env,
            timeout=60,
        )

        # If indexing succeeded, try searching
        if index_result.returncode == 0:
            search_result = subprocess.run(
                [
                    "python",
                    "-m",
                    "pr_verification_agent.cli",
                    "search",
                    "hello world",
                    "--limit",
                    "3",
                ],
                capture_output=True,
                text=True,
                cwd=git_repo,
                env=env,
            )

            # Should either find results or handle gracefully
            assert (
                search_result.returncode == 0 or "Search failed" in search_result.stdout
            )
