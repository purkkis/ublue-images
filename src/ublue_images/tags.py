from pathlib import Path

from loguru import logger

from ublue_images.github_release_download import GitHubReleaseDownloader, ReleaseItems


def refresh_tags() -> None:
    """
    Refreshes tagged release metadata from GitHub.
    """
    logger.info("Starting tags refresh process")
    ghd = GitHubReleaseDownloader()
    config_path = Path(__file__).with_name("tags.json")
    tags_data = ghd.load_config(config_path, ReleaseItems)
    for t in tags_data.items:
        if not t.repo:
            logger.warning(f"Skipping item without repo: {t.name}")
            continue
        latest_tag = ghd.latest_tag(t.repo)
        if latest_tag == t.tag:
            logger.info(f"Tag for {t.repo} is already up to date: {t.tag}")
            continue
        logger.info(f"New tag for {t.repo}: {latest_tag}, old tag: {t.tag}")
        t.tag = latest_tag
        release_data = ghd.get_latest_release(t.repo)
        t.url = ghd.get_rpm_download_url(release_data)
    config_path.write_text(tags_data.model_dump_json(indent=2))
    logger.info("Tags refresh process completed")


def download_releases() -> None:
    """
    Downloads RPM assets from the tagged release configuration.
    """
    logger.info("Starting releases download process")
    ghd = GitHubReleaseDownloader()
    config_path = Path(__file__).with_name("tags.json")
    download_config = ghd.load_config(config_path, ReleaseItems)
    ghd.download_files(download_config, output="files/dnf/tags")
    logger.info("Releases download process completed")
