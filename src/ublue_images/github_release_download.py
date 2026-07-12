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


class DownloadableReleaseItem(BaseModel):
    name: str
    tag: str
    url: str
    enabled: bool = True


class GithubReleaseItem(DownloadableReleaseItem):
    repo: str | None = None
    rpm_suffix: str = "x86_64.rpm"


class DirectDownloadItem(DownloadableReleaseItem):
    pass


class GithubReleaseItems(BaseModel):
    items: list[GithubReleaseItem] = Field(default_factory=list)


class DirectDownloadItems(BaseModel):
    items: list[DirectDownloadItem] = Field(default_factory=list)


class ReleasesConfig(BaseModel):
    github_releases: GithubReleaseItems = Field(default_factory=GithubReleaseItems)
    direct_downloads: DirectDownloadItems = Field(default_factory=DirectDownloadItems)


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
    def get_rpm_download_url(release_data: GithubReleases, rpm_suffix: str) -> str:
        """
        Extract the download URL for an RPM asset whose name ends with with the given 'rpm_suffix'.
        """
        try:
            for asset in release_data.assets:
                if asset.name.endswith(rpm_suffix) and asset.content_type == "application/x-rpm":
                    return asset.browser_download_url
            raise ValueError(f"No RPM asset found with suffix {rpm_suffix!r}")
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

    def download_file_to_local_dir(self, file_config: DownloadableReleaseItem, output: str) -> None:
        local_path = Path(output) / file_config.name
        bytes_written = self.download(file_config.url, file_config.name, local_path)
        logger.info(f"Wrote {bytes_written} bytes for {file_config.name} to {local_path}")

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


if __name__ == "__main__":
    ghd = GitHubReleaseDownloader()
    r: GithubReleases = ghd.get_latest_release("dbeaver/dbeaver")
    print(r.tag_name)
    for asset in r.assets:
        print(asset.name)
        print(asset.content_type)
        print("-" * 50)
