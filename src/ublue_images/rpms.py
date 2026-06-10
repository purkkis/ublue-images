from pathlib import Path

from loguru import logger

from ublue_images.github_release_download import GitHubReleaseDownloader, ReleaseItems


def rpms() -> None:
    """
    Downloads RPM assets from the fixed release configuration.
    """
    logger.info("Starting RPMs download process")
    ghd = GitHubReleaseDownloader()
    config_path = Path(__file__).with_name("files.json")
    download_config = ghd.load_config(config_path, ReleaseItems)
    ghd.download_files(download_config)
    logger.info("RPMs download process completed")
