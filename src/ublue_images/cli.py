from __future__ import annotations

from collections.abc import Callable

import typer
from loguru import logger

from ublue_images.rpms import rpms as download_rpms
from ublue_images.tags import download_releases, refresh_tags

app = typer.Typer(
    help="Helper commands for refreshing release metadata and downloading RPMs.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
rpms_app = typer.Typer(
    help="Download fixed RPM artifacts.",
    no_args_is_help=True,
    rich_markup_mode=None,
)
tags_app = typer.Typer(
    help="Manage tagged GitHub release downloads.",
    no_args_is_help=True,
    rich_markup_mode=None,
)

app.add_typer(tags_app, name="tags")
app.add_typer(rpms_app, name="rpms")


def _run_command(command: Callable[[], None], error_message: str) -> None:
    """Runs a command handler and converts exceptions into CLI exit codes.

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


@tags_app.command("refresh")
def refresh_tags_command() -> None:
    _run_command(refresh_tags, "Tag refresh failed")


@tags_app.command("download")
def download_tags_command() -> None:
    _run_command(download_releases, "Tagged release download failed")


@rpms_app.command("download")
def download_rpms_command() -> None:
    _run_command(download_rpms, "RPM download failed")


def main() -> None:
    """Runs the Typer application."""
    app()


if __name__ == "__main__":
    main()
