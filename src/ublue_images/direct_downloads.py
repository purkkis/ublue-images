from loguru import logger

from ublue_images.github_release_download import GitHubReleaseDownloader, load_releases_config


def download_direct_downloads() -> None:
    """
    Downloads RPM assets listed under direct_downloads in releases.json.
    """
    logger.info("Starting direct_downloads download")
    ghd = GitHubReleaseDownloader()
    download_config = load_releases_config().direct_downloads
    ghd.download_files(download_config, output="files/dnf/direct_downloads")
    logger.info("direct_downloads download completed")
