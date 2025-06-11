"""Configuration management for the PR Verification Agent."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv


class JiraConfig(BaseSettings):
    """Jira integration configuration."""

    server_url: Optional[str] = Field(None, alias="JIRA_SERVER_URL")
    email: Optional[str] = Field(None, alias="JIRA_EMAIL")
    api_token: Optional[str] = Field(None, alias="JIRA_API_TOKEN")


class GitHubConfig(BaseSettings):
    """GitHub integration configuration."""

    token: Optional[str] = Field(None, alias="GITHUB_TOKEN")


class AIConfig(BaseSettings):
    """AI model configuration."""

    openai_api_key: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    default_provider: str = Field("openai", alias="DEFAULT_AI_PROVIDER")


class RedisConfig(BaseSettings):
    """Redis configuration for vector database using RedisVL."""

    url: str = Field("redis://localhost:6379", alias="REDIS_URL")
    host: str = Field("localhost", alias="REDIS_HOST")
    port: int = Field(6379, alias="REDIS_PORT")
    password: Optional[str] = Field(None, alias="REDIS_PASSWORD")
    db: int = Field(0, alias="REDIS_DB")
    max_connections: int = Field(20, alias="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(30, alias="REDIS_SOCKET_TIMEOUT")

    @property
    def connection_url(self) -> str:
        """Generate Redis connection URL from components."""
        if self.url != "redis://localhost:6379":
            return self.url

        auth_part = f":{self.password}@" if self.password else ""
        return f"redis://{auth_part}{self.host}:{self.port}/{self.db}"


class RepositoryConfig(BaseSettings):
    """Repository indexing configuration for RedisVL."""

    # Index configuration
    index_name: str = Field("pr_agent_codebase", alias="REPO_INDEX_NAME")
    index_prefix: str = Field("codebase_docs", alias="REPO_INDEX_PREFIX")

    # Processing configuration
    index_batch_size: int = Field(100, alias="REPO_INDEX_BATCH_SIZE")
    max_file_size_mb: int = Field(10, alias="REPO_MAX_FILE_SIZE_MB")
    excluded_dirs: str = Field(
        ".git,node_modules,__pycache__,.pytest_cache,build,dist,target,.venv,venv",
        alias="REPO_EXCLUDED_DIRS",
    )
    included_extensions: str = Field(
        ".py,.js,.ts,.java,.cpp,.c,.h,.hpp,.cs,.go,.rs,.rb,.php,.swift,.kt,.scala",
        alias="REPO_INCLUDED_EXTENSIONS",
    )

    # Vector configuration
    vectorizer: str = Field("sentence-transformers", alias="REPO_VECTORIZER")
    embedding_model: str = Field("all-MiniLM-L6-v2", alias="REPO_EMBEDDING_MODEL")
    vector_dims: int = Field(
        384, alias="REPO_VECTOR_DIMS"
    )  # all-MiniLM-L6-v2 dimensions
    distance_metric: str = Field("cosine", alias="REPO_DISTANCE_METRIC")
    vector_algorithm: str = Field("hnsw", alias="REPO_VECTOR_ALGORITHM")

    # Chunking configuration
    chunk_size: int = Field(512, alias="REPO_CHUNK_SIZE")
    chunk_overlap: int = Field(50, alias="REPO_CHUNK_OVERLAP")

    @property
    def excluded_dirs_list(self) -> list[str]:
        """Get excluded directories as a list."""
        return [d.strip() for d in self.excluded_dirs.split(",")]

    @property
    def included_extensions_list(self) -> list[str]:
        """Get included extensions as a list."""
        return [e.strip() for e in self.included_extensions.split(",")]


class AppConfig(BaseSettings):
    """Application configuration."""

    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_format: str = Field("json", alias="LOG_FORMAT")
    max_retries: int = Field(3, alias="MAX_RETRIES")
    request_timeout: int = Field(30, alias="REQUEST_TIMEOUT")
    cache_ttl: int = Field(300, alias="CACHE_TTL")


class Config:
    """Main configuration class that combines all configuration sections."""

    def __init__(self, env_file: Optional[str] = None):
        """Initialize configuration.

        Args:
            env_file: Path to .env file. If None, looks for .env in current directory.
        """
        if env_file is None:
            env_file = Path.cwd() / ".env"

        if Path(env_file).exists():
            load_dotenv(env_file)

        self.jira = JiraConfig()
        self.github = GitHubConfig()
        self.ai = AIConfig()
        self.redis = RedisConfig()
        self.repository = RepositoryConfig()
        self.app = AppConfig()

    def validate(self) -> None:
        """Validate configuration and raise errors for missing required values."""
        errors = []

        # Validate Jira configuration
        if not self.jira.server_url:
            errors.append("JIRA_SERVER_URL is required")
        if not self.jira.email:
            errors.append("JIRA_EMAIL is required")
        if not self.jira.api_token:
            errors.append("JIRA_API_TOKEN is required")

        # Validate GitHub configuration
        if not self.github.token:
            errors.append("GITHUB_TOKEN is required")

        # Validate AI provider configuration
        if self.ai.default_provider == "openai" and not self.ai.openai_api_key:
            errors.append(
                "OPENAI_API_KEY is required when using OpenAI as default provider"
            )
        elif self.ai.default_provider == "anthropic" and not self.ai.anthropic_api_key:
            errors.append(
                "ANTHROPIC_API_KEY is required when using Anthropic as default provider"
            )

        if self.ai.default_provider not in ["openai", "anthropic"]:
            errors.append(
                f"Invalid AI provider: {self.ai.default_provider}. "
                "Must be 'openai' or 'anthropic'"
            )

        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"- {error}" for error in errors
            )
            raise ValueError(error_msg)


# Global configuration instance
config = Config()
