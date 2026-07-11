from loguru import logger

from ublue_images.github_release_download import (
    GitHubReleaseDownloader,
    load_releases_config,
    save_releases_config,
)


def refresh_github_releases() -> None:
    """
    Refreshes github_releases metadata from GitHub.
    """
    logger.info("Starting github_releases refresh")
    ghd = GitHubReleaseDownloader()
    releases_config = load_releases_config()
    github_releases = releases_config.github_releases
    for item in github_releases.items:
        if not item.repo:
            logger.warning(f"Skipping item without repo: {item.name}")
            continue
        latest_tag = ghd.latest_tag(item.repo)
        if latest_tag == item.tag:
            logger.info(f"Tag for {item.repo} is already up to date: {item.tag}")
            continue
        logger.info(f"New tag for {item.repo}: {latest_tag}, old tag: {item.tag}")
        item.tag = latest_tag
        release_data = ghd.get_latest_release(item.repo)
        item.url = ghd.get_rpm_download_url(release_data)
    save_releases_config(releases_config)
    logger.info("github_releases refresh completed")


def download_github_releases() -> None:
    """
    Downloads RPM assets listed under github_releases in releases.json.
    """
    logger.info("Starting github_releases download")
    ghd = GitHubReleaseDownloader()
    download_config = load_releases_config().github_releases
    ghd.download_files(download_config, output="files/dnf/github_releases")
    logger.info("github_releases download completed")
