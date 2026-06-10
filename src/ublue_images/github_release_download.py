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
        try:
            response = requests.get(url)
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
    def download(url: str, file_name: str) -> bytes:
        """Downloads a file from a URL.

        Args:
            url: The URL to download.
            file_name: A human-readable filename used for logging.

        Returns:
            The downloaded file content.
        """
        logger.info(f"Downloading {file_name}...")
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def download_file_to_local_dir(
        self, file_config: ReleaseItem, output: str = "files/dnf/rpms"
    ) -> None:
        local_path = os.path.join(output, file_config.name)
        content = self.download(file_config.url, file_config.name)
        with open(local_path, "wb") as file_handle:
            file_handle.write(content)
        logger.info(f"Wrote {len(content)} bytes for {file_config.name} to {local_path}")

    def download_files(self, config: ReleaseItems, output: str = "files/dnf/rpms") -> None:
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
                logger.info(
                    f"Skipping download of disabled file: {file_config.name} (tag: {file_config.tag})"
                )
                continue
            self.download_file_to_local_dir(file_config, output=output)

    def latest_tag(self, repo: str) -> str:
        tag: str = self.get_latest_release(repo).tag_name
        if not isinstance(tag, str):
            raise ValueError(f"Expected string tag, got {type(tag)}")
        if not tag.strip():
            raise ValueError("Tag is empty or whitespace only")
        return tag
