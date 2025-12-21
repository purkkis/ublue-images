from argparse import ArgumentParser
from pathlib import Path

from loguru import logger

from ublue_images.github_release_download import GitHubReleaseDownloader, ReleaseItems


def refresh_tags():
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
        t.tag = latest_tag
        release_data = ghd.get_latest_release(t.repo)
        t.url = ghd.get_rpm_download_url(release_data)
    config_path.write_text(tags_data.model_dump_json(indent=2))


def download_releases():
    ghd = GitHubReleaseDownloader()
    config_path = Path(__file__).with_name("tags.json")
    download_config = ghd.load_config(config_path, ReleaseItems)
    ghd.download_files(download_config, output="files/dnf/tags")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Refresh tags")
    parser.add_argument("--download", action="store_true", help="Download releases")
    args = parser.parse_args()

    if args.refresh:
        refresh_tags()
    elif args.download:
        download_releases()
