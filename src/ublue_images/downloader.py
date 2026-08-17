import fnmatch
import os
import shutil
from pathlib import Path
from typing import TypeVar

import requests
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

from ublue_images.chatwise import ChatWiseReleaseItem, download_rpm
from ublue_images.models.github import GithubReleases
from ublue_images.utils import REQUEST_TIMEOUT, download_file

load_dotenv()

RELEASES_JSON_SCHEMA = "releases_schema.json"


# Common fields for all release items
class DownloadableReleaseItem(BaseModel):
    name: str
    tag: str
    url: str
    enabled: bool = True


# Specific fields for GitHub releases
class GithubReleaseItem(DownloadableReleaseItem):
    repo: str | None = None
    rpm_suffix: str = "x86_64.rpm"


# Specific fields for direct downloads
# (no additional fields)
class DirectDownloadItem(DownloadableReleaseItem):
    pass


class GithubReleaseItems(BaseModel):
    items: list[GithubReleaseItem] = Field(default_factory=list)


class DirectDownloadItems(BaseModel):
    items: list[DirectDownloadItem] = Field(default_factory=list)


class ReleasesConfig(BaseModel):
    schema_ref: str = Field(default=RELEASES_JSON_SCHEMA, alias="$schema")
    github_releases: GithubReleaseItems = Field(default_factory=GithubReleaseItems)
    direct_downloads: DirectDownloadItems = Field(default_factory=DirectDownloadItems)
    chatwise: ChatWiseReleaseItem = Field(default_factory=ChatWiseReleaseItem)


def release_config_json_schema():
    with open(RELEASES_JSON_SCHEMA, "w") as file:
        import json

        file.write(json.dumps(ReleasesConfig.model_json_schema(), indent=2))


def load_releases_config() -> ReleasesConfig:
    return ReleasesConfig.model_validate_json(Path("releases.json").read_text(encoding="utf-8"))


def save_releases_config(config: ReleasesConfig) -> None:
    Path("releases.json").write_text(f"{config.model_dump_json(indent=2, by_alias=True)}\n", encoding="utf-8")


T = TypeVar("T", bound=BaseModel)


class GitHubReleaseDownloader:
    @staticmethod
    def load_config(path: Path, model: type[T]) -> T:
        """
        Loads and validates a JSON configuration file.
        Returns:
            `TypeVar("T", bound=BaseModel)`
        """
        return model.model_validate_json(path.read_text(encoding="utf-8"))

    @staticmethod
    def get_latest_release(repo: str) -> GithubReleases:
        """
        Fetch the latest release information for a GitHub repository.
        Returns:
            GithubReleases model
        """
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        logger.info(f"Fetching latest release for {repo} from {url}")
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)  # timeout = (connect timeout, read timeout)
            response.raise_for_status()
            return GithubReleases.model_validate(response.json())
        except Exception as e:
            logger.error(f"Error fetching latest release for {repo}: {e}")
            raise

    @staticmethod
    def get_rpm_download_url(release_data: GithubReleases, rpm_suffix: str) -> str:
        """
        Extract the download URL for an RPM asset whose name matches the glob in rpm_suffix.

        If rpm_suffix does not start with '*', a leading '*' is prepended so values like
        x86_64.rpm match asset names ending with that suffix.
        """
        pattern = rpm_suffix if rpm_suffix.startswith("*") else f"*{rpm_suffix}"
        try:
            for asset in release_data.assets:
                if fnmatch.fnmatch(asset.name, pattern):
                    return asset.browser_download_url
            raise ValueError(f"No RPM asset found matching pattern {pattern!r}")
        except Exception as e:
            logger.error(f"Error extracting RPM download URL: {e}")
            raise

    @staticmethod
    def download(url: str, file_name: str, destination: Path) -> int:
        logger.info(f"Downloading {file_name}...")
        return download_file(url, destination)

    def download_file_to_local_dir(self, file_config: DownloadableReleaseItem, output: str) -> None:
        local_path = Path(output) / file_config.name
        self.download(file_config.url, file_config.name, local_path)

    def download_files(self, config: GithubReleaseItems | DirectDownloadItems, output: str) -> None:
        """
        Downloads all enabled RPMs from the supplied configuration.
        """
        logger.info(f"Starting download of {len(config.items)} files to {output}")
        if os.path.exists(output):
            logger.info(f"Removing output directory: {output}")
            shutil.rmtree(output)
        logger.info(f"Created output directory: {output}")
        os.makedirs(output)

        for file_config in config.items:
            if not file_config.enabled:
                logger.info(f"Skipping download of disabled file: {file_config.name} (tag: {file_config.tag})")
                continue
            self.download_file_to_local_dir(file_config, output=output)

    def latest_tag(self, repo: str) -> str:
        tag: str = self.get_latest_release(repo).tag_name
        if not tag.strip():
            raise ValueError("Tag is empty or whitespace only")
        return tag


def refresh_github_releases() -> None:
    """
    Refreshes github_releases metadata from GitHub.
    """
    logger.info("Starting github_releases refresh")
    ghd = GitHubReleaseDownloader()
    releases_config: ReleasesConfig = load_releases_config()
    github_releases: GithubReleaseItems = releases_config.github_releases
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
        item.url = ghd.get_rpm_download_url(release_data, rpm_suffix=item.rpm_suffix)
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


def download_direct_downloads() -> None:
    """
    Downloads RPM assets listed under direct_downloads in releases.json.
    """
    logger.info("Starting direct_downloads download")
    ghd = GitHubReleaseDownloader()
    download_config = load_releases_config().direct_downloads
    ghd.download_files(download_config, output="files/dnf/direct_downloads")
    logger.info("direct_downloads download completed")


def download_chatwise() -> None:
    """
    Downloads the latest ChatWise RPM without caching its release metadata.
    """
    logger.info("Starting ChatWise download")
    download_rpm(load_releases_config().chatwise, Path("files/dnf/direct_downloads/chatwise.rpm"))
    logger.info("ChatWise download completed")


if __name__ == "__main__":
    ghd = GitHubReleaseDownloader()
    r: GithubReleases = ghd.get_latest_release("dbeaver/dbeaver")
    print(r.tag_name)
    for asset in r.assets:
        print(asset.name)
        print(asset.content_type)
        print("-" * 50)
