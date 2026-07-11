import os
import shutil
from pathlib import Path
from typing import TypeVar

import requests
from dotenv import load_dotenv
from loguru import logger
from pydantic import BaseModel, Field

from ublue_images.models.github import GithubReleases

load_dotenv()


class ReleaseItem(BaseModel):
    name: str
    tag: str
    url: str
    repo: str | None = None
    enabled: bool = True


class ReleaseItems(BaseModel):
    items: list[ReleaseItem] = Field(default_factory=list)


class ReleasesConfig(BaseModel):
    github_releases: ReleaseItems = Field(default_factory=ReleaseItems)
    direct_downloads: ReleaseItems = Field(default_factory=ReleaseItems)


def load_releases_config() -> ReleasesConfig:
    return ReleasesConfig.model_validate_json(Path("releases.json").read_text(encoding="utf-8"))


def save_releases_config(config: ReleasesConfig) -> None:
    Path("releases.json").write_text(f"{config.model_dump_json(indent=2)}\n", encoding="utf-8")


T = TypeVar("T", bound=BaseModel)

REQUEST_TIMEOUT = (5, 60)
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


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
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)  # timeout = (connect timeout, read timeout)
            response.raise_for_status()
            return GithubReleases.model_validate(response.json())
        except Exception as e:
            logger.error(f"Error fetching latest release for {repo}: {e}")
            raise e

    @staticmethod
    def get_rpm_download_url(release_data: GithubReleases) -> str:
        """
        Extract the download URL for x86_64 RPM assets from release data.
        """
        try:
            for asset in release_data.assets:
                if asset.name.endswith("x86_64.rpm"):
                    return asset.browser_download_url
            raise ValueError("No x86_64 RPM asset found")
        except Exception as e:
            logger.error(f"Error extracting RPM download URL: {e}")
            raise e

    @staticmethod
    def download(url: str, file_name: str, destination: Path) -> int:
        """
        Downloads a file from a URL to a local path.

        Args:
            url: The URL to download.
            file_name: A human-readable filename used for logging.
            destination: The path to write the downloaded file to.

        Returns:
            The number of bytes written.
        """
        logger.info(f"Downloading {file_name}...")
        bytes_written = 0
        with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
            response.raise_for_status()
            with destination.open("wb") as file_handle:
                for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                    if not chunk:
                        continue
                    bytes_written += len(chunk)
                    file_handle.write(chunk)
        return bytes_written

    def download_file_to_local_dir(self, file_config: ReleaseItem, output: str) -> None:
        local_path = Path(output) / file_config.name
        bytes_written = self.download(file_config.url, file_config.name, local_path)
        logger.info(f"Wrote {bytes_written} bytes for {file_config.name} to {local_path}")

    def download_files(self, config: ReleaseItems, output: str) -> None:
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
