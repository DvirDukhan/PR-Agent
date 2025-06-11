"""Command-line interface for the PR Verification Agent."""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .core.config import config
from .core.logging import setup_logging, get_logger


console = Console()
logger = get_logger(__name__)


@click.group()
@click.option(
    "--config-file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Set logging level",
)
@click.option("--log-file", type=click.Path(path_type=Path), help="Path to log file")
@click.version_option()
def cli(
    config_file: Optional[Path], log_level: Optional[str], log_file: Optional[Path]
) -> None:
    """PR Verification Agent - Verify GitHub PRs against Jira Definition of Done."""
    try:
        # Setup logging
        setup_logging(level=log_level, log_file=str(log_file) if log_file else None)

        # Validate configuration
        config.validate()

        logger.info(
            "PR Verification Agent initialized",
            config_file=str(config_file) if config_file else None,
        )

    except Exception as e:
        console.print(f"[red]Configuration error: {e}[/red]")
        sys.exit(1)


@cli.command()
def chat() -> None:
    """Start interactive chat mode for PR verification."""
    console.print(
        Panel.fit(
            Text("🤖 PR Verification Agent", style="bold blue"),
            subtitle="Interactive Chat Mode",
        )
    )

    console.print("\n[green]Welcome to the PR Verification Agent![/green]")
    console.print("I can help you:")
    console.print("• Analyze and improve Jira Definition of Done quality")
    console.print("• Verify GitHub pull requests against DoD requirements")
    console.print("• Provide confidence scores and improvement suggestions")
    console.print("\nType 'help' for available commands or 'quit' to exit.\n")

    try:
        from .agents.chat_agent import ChatAgent

        chat_agent = ChatAgent()
        chat_agent.start_conversation()
    except ImportError:
        console.print("[yellow]Chat agent not yet implemented. Coming soon![/yellow]")
        console.print("This will be the main interactive interface for the agent.")


@cli.command()
@click.argument("jira_ticket")
def analyze_dod(jira_ticket: str) -> None:
    """Analyze Definition of Done quality for a Jira ticket.

    Args:
        jira_ticket: Jira ticket ID (e.g., PROJ-123)
    """
    console.print(
        f"[blue]Analyzing Definition of Done for ticket: {jira_ticket}[/blue]"
    )

    try:
        # TODO: Implement DoD analysis
        console.print("[yellow]DoD analysis not yet implemented. Coming soon![/yellow]")
        console.print(f"This will analyze the Definition of Done for {jira_ticket}")
        console.print("and provide suggestions for improvement.")

    except Exception as e:
        logger.error("Failed to analyze DoD", ticket=jira_ticket, error=str(e))
        console.print(f"[red]Error analyzing DoD: {e}[/red]")


@cli.command()
@click.argument("pr_url")
@click.option("--jira-ticket", help="Associated Jira ticket ID")
def verify_pr(pr_url: str, jira_ticket: Optional[str]) -> None:
    """Verify a GitHub pull request against Definition of Done.

    Args:
        pr_url: GitHub pull request URL
        jira_ticket: Optional Jira ticket ID for DoD reference
    """
    console.print(f"[blue]Verifying PR: {pr_url}[/blue]")
    if jira_ticket:
        console.print(f"[blue]Against Jira ticket: {jira_ticket}[/blue]")

    try:
        # TODO: Implement PR verification
        console.print(
            "[yellow]PR verification not yet implemented. Coming soon![/yellow]"
        )
        console.print(f"This will verify {pr_url} against the Definition of Done")
        if jira_ticket:
            console.print(f"from Jira ticket {jira_ticket}")
        console.print("and provide a confidence score with improvement suggestions.")

    except Exception as e:
        logger.error(
            "Failed to verify PR", pr_url=pr_url, ticket=jira_ticket, error=str(e)
        )
        console.print(f"[red]Error verifying PR: {e}[/red]")


@cli.command()
@click.option("--initialize", is_flag=True, help="Initialize repository indexing")
@click.option("--update", is_flag=True, help="Update existing repository index")
@click.option("--force", is_flag=True, help="Force reindexing even if up to date")
def index(initialize: bool, update: bool, force: bool) -> None:
    """Index repository for context-aware analysis using RedisVL."""
    if not initialize and not update:
        console.print("[red]Please specify either --initialize or --update[/red]")
        return

    try:
        import asyncio
        from .core.repository import RepositoryIndexer

        async def run_indexing():
            if initialize or update:
                console.print(
                    "[blue]Starting repository indexing with RedisVL...[/blue]"
                )

                # Check if we're in a Git repository
                indexer = RepositoryIndexer()
                try:
                    indexer.validate_repository()
                    console.print(
                        f"[green]✓ Found Git repository at {indexer.repo_path}[/green]"
                    )
                except Exception as e:
                    console.print(f"[red]✗ Repository validation failed: {e}[/red]")
                    return

                # Run indexing
                with console.status("[bold green]Indexing repository..."):
                    stats = await indexer.index_repository(force_reindex=force)

                console.print("\n[green]✓ Repository indexing completed![/green]")
                console.print(f"• Files indexed: {stats['total_files']}")
                console.print(f"• Code chunks: {stats['total_chunks']}")
                console.print(f"• Index name: {stats['index_name']}")
                console.print(f"• Repository: {stats['repository_path']}")

        # Run the async indexing
        asyncio.run(run_indexing())

    except ImportError as e:
        console.print(f"[red]Missing dependencies: {e}[/red]")
        console.print("Please install required packages: pip install redisvl GitPython")
    except Exception as e:
        logger.error("Indexing failed", error=str(e))
        console.print(f"[red]Indexing failed: {e}[/red]")


@cli.command()
@click.argument("query")
@click.option(
    "--semantic", is_flag=True, help="Use semantic vector search", default=True
)
@click.option("--limit", default=10, help="Number of results to return")
@click.option("--language", help="Filter by programming language")
@click.option("--file-type", help="Filter by file extension")
def search(
    query: str, semantic: bool, limit: int, language: str, file_type: str
) -> None:
    """Search repository code and documentation using RedisVL."""
    search_type = "semantic vector" if semantic else "keyword"
    console.print(f"[blue]Searching repository ({search_type}): {query}[/blue]")

    try:
        import asyncio
        from .core.vector_store import search_codebase

        async def run_search():
            # Build filters
            filters = {}
            if language:
                filters["language"] = language
            if file_type:
                filters["file_extension"] = (
                    file_type if file_type.startswith(".") else f".{file_type}"
                )

            with console.status("[bold green]Searching codebase..."):
                results = await search_codebase(query, limit=limit, filters=filters)

            if not results:
                console.print("[yellow]No results found.[/yellow]")
                return

            console.print(f"\n[green]Found {len(results)} results:[/green]\n")

            for i, result in enumerate(results, 1):
                distance = result.get("vector_distance", 0)
                similarity = max(0, 1 - distance) * 100

                console.print(f"[bold]{i}. {result.get('file_path', 'Unknown')}[/bold]")
                console.print(f"   Language: {result.get('language', 'Unknown')}")
                console.print(f"   Similarity: {similarity:.1f}%")

                if result.get("function_name"):
                    console.print(f"   Function: {result['function_name']}")
                if result.get("class_name"):
                    console.print(f"   Class: {result['class_name']}")

                # Show content preview
                content = result.get("content", "")
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                    console.print(f"   Preview: {preview}")

                console.print()

        # Run the async search
        asyncio.run(run_search())

    except ImportError as e:
        console.print(f"[red]Missing dependencies: {e}[/red]")
        console.print(
            "Please install required packages and initialize the index first."
        )
    except Exception as e:
        logger.error("Search failed", error=str(e))
        console.print(f"[red]Search failed: {e}[/red]")
        console.print(
            "Make sure the repository is indexed first: pr-agent index --initialize"
        )


@cli.command()
def status() -> None:
    """Show repository indexing status and statistics using RedisVL."""
    console.print("[blue]Repository Status[/blue]\n")

    try:
        import asyncio
        from .core.vector_store import CodebaseVectorStore
        from .core.repository import RepositoryIndexer

        async def show_status():
            # Check repository
            try:
                indexer = RepositoryIndexer()
                indexer.validate_repository()
                console.print(f"[green]✓ Repository: {indexer.repo_path}[/green]")
            except Exception as e:
                console.print(f"[red]✗ Repository: {e}[/red]")
                return

            # Check vector store
            try:
                store = CodebaseVectorStore(use_async=True)
                await store.initialize()
                stats = await store.get_stats()

                console.print("[green]✓ Vector Store Connected[/green]")
                console.print(f"  Index Name: {stats.get('index_name', 'Unknown')}")
                console.print(f"  Total Documents: {stats.get('total_documents', 0)}")
                console.print(f"  Index Size: {stats.get('index_size_mb', 0):.2f} MB")
                console.print(
                    f"  Vector Index Size: {stats.get('vector_index_size_mb', 0):.2f} MB"
                )

            except Exception as e:
                console.print(f"[red]✗ Vector Store: {e}[/red]")
                console.print("Run 'pr-agent index --initialize' to create the index")

        # Run the async status check
        asyncio.run(show_status())

    except ImportError as e:
        console.print(f"[red]Missing dependencies: {e}[/red]")
    except Exception as e:
        logger.error("Status check failed", error=str(e))
        console.print(f"[red]Status check failed: {e}[/red]")


@cli.command()
def config_check() -> None:
    """Check configuration and connectivity to external services."""
    console.print("[blue]Checking configuration and service connectivity...[/blue]\n")

    # Check Repository configuration
    console.print("📁 [bold]Repository Configuration[/bold]")
    try:
        console.print(f"  Embedding Model: {config.repository.embedding_model}")
        console.print(f"  Chunk Size: {config.repository.chunk_size}")
        console.print(f"  Max File Size: {config.repository.max_file_size_mb}MB")
        console.print("  Repository Detection: [yellow]Not tested yet[/yellow]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")

    # Check Redis configuration
    console.print("\n🔍 [bold]Redis Configuration[/bold]")
    try:
        console.print(f"  Host: {config.redis.host}")
        console.print(f"  Port: {config.redis.port}")
        console.print(f"  Database: {config.redis.db}")
        console.print("  Connectivity: [yellow]Not tested yet[/yellow]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")

    # Check Jira configuration
    console.print("\n🔍 [bold]Jira Configuration[/bold]")
    try:
        console.print(f"  Server URL: {config.jira.server_url}")
        console.print(f"  Email: {config.jira.email}")
        console.print("  API Token: [green]✓ Configured[/green]")
        # TODO: Test Jira connectivity
        console.print("  Connectivity: [yellow]Not tested yet[/yellow]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")

    # Check GitHub configuration
    console.print("\n🔍 [bold]GitHub Configuration[/bold]")
    try:
        console.print("  Token: [green]✓ Configured[/green]")
        # TODO: Test GitHub connectivity
        console.print("  Connectivity: [yellow]Not tested yet[/yellow]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")

    # Check AI configuration
    console.print("\n🔍 [bold]AI Configuration[/bold]")
    try:
        console.print(f"  Default Provider: {config.ai.default_provider}")
        if config.ai.openai_api_key:
            console.print("  OpenAI API Key: [green]✓ Configured[/green]")
        if config.ai.anthropic_api_key:
            console.print("  Anthropic API Key: [green]✓ Configured[/green]")
        # TODO: Test AI service connectivity
        console.print("  Connectivity: [yellow]Not tested yet[/yellow]")
    except Exception as e:
        console.print(f"  [red]✗ Error: {e}[/red]")


def main() -> None:
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
