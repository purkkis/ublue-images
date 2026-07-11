from loguru import logger

from ublue_images.github_release_download import GitHubReleaseDownloader, load_releases_config


def rpms() -> None:
    """
    Downloads RPM assets from the fixed release configuration.
    """
    logger.info("Starting RPMs download process")
    ghd = GitHubReleaseDownloader()
    download_config = load_releases_config().direct_downloads
    ghd.download_files(download_config)
    logger.info("RPMs download process completed")
