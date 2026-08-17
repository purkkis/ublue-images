from collections.abc import Callable

import typer
from loguru import logger

from ublue_images.downloader import (
    download_chatwise,
    download_direct_downloads,
    download_github_releases,
    refresh_github_releases,
    release_config_json_schema,
)

app = typer.Typer(
    help="Helper commands for refreshing release metadata and downloading RPMs.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
direct_downloads_app = typer.Typer(
    help="Download RPMs from direct_download URLs in releases.json.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
chatwise_app = typer.Typer(
    help="Download the latest ChatWise RPM.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
github_releases_app = typer.Typer(
    help="Refresh and download github_releases entries in releases.json.",
    no_args_is_help=True,
    rich_markup_mode=None,
)

app.add_typer(github_releases_app, name="github-releases")
app.add_typer(direct_downloads_app, name="direct-downloads")
app.add_typer(chatwise_app, name="chatwise")


def _run_command(command: Callable[[], None], error_message: str) -> None:
    """
    Runs a command handler and converts exceptions into CLI exit codes.

    Args:
        command: The no-argument function that performs the command work.
        error_message: The message logged when the command raises an exception.

    Raises:
        typer.Exit: Raised with a non-zero code if the command fails.
    """
    try:
        command()
    except Exception:
        logger.exception(error_message)
        raise typer.Exit(code=1) from None


@github_releases_app.command("refresh")
def refresh_github_releases_command() -> None:
    _run_command(refresh_github_releases, "github_releases refresh failed")


@github_releases_app.command("download")
def download_github_releases_command() -> None:
    _run_command(download_github_releases, "github_releases download failed")


@direct_downloads_app.command("download")
def download_direct_downloads_command() -> None:
    _run_command(download_direct_downloads, "direct_downloads download failed")


@chatwise_app.command("download")
def download_chatwise_command() -> None:
    _run_command(download_chatwise, "ChatWise download failed")


@app.command("schema")
def release_config_json_schema_command() -> None:
    _run_command(release_config_json_schema, "release config JSON schema failed")
