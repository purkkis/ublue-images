import tempfile
from typing import Optional

import awswrangler as wr
import requests
from loguru import logger
from pydantic import BaseModel

from ublue_images.models.github import Model


class File(BaseModel):
    name: str
    url: str


class DownloadFiles(BaseModel):
    files: list[File]


class GitHubReleaseDownloader:
    download_cache: dict[str, str] = {}

    @staticmethod
    def get_latest_release(repo: str) -> Optional[Model]:
        """Fetch the latest release information for a GitHub repository."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return Model.model_validate_json(response.json())
        except requests.RequestException as e:
            logger.error(f"Error fetching latest release for {repo}: {e}")
            return None

    @staticmethod
    def get_rpm_download_url(release_data: Model) -> Optional[str]:
        """Extract the download URL for x86_64 RPM assets from release data."""
        try:
            for asset in release_data.assets:
                if asset.name.endswith("x86_64.rpm"):
                    return asset.browser_download_url
            return None
        except Exception as e:
            logger.error(f"Error extracting RPM download URL: {e}")
            return None

    def download_file_to_tmp_dir(self, url: str, file: str):
        """
        Downloads a file into a tmp directory, and returns the file path

        Args:
            url (str): The URL of the file to download

        Returns:
            str: The path to the downloaded file
        """
        try:
            with tempfile.NamedTemporaryFile() as tmp_file:
                logger.info(f"Downloading {file}...")
                response = requests.get(url)
                response.raise_for_status()
                tmp_file.write(response.content)
                tmp_file_path = tmp_file.name
                wr.s3.upload(local_file=tmp_file_path, path=f"s3://bluebuild-files/{file}")
            self.download_cache[file] = tmp_file_path
        except requests.RequestException as e:
            logger.error(f"Error downloading file from {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating temporary file for {url}: {e}")
            raise

    def download_files(self, config: DownloadFiles):
        for file_config in config.files:
            self.download_file_to_tmp_dir(file_config.url, file_config.name)


if __name__ == "__main__":
    ghd = GitHubReleaseDownloader()

    # Example usage
    download_config = DownloadFiles(
        files=[
            File(
                name="opencode.rpm",
                url="https://github.com/sst/opencode/releases/download/v1.0.164/opencode-desktop-linux-x86_64.rpm",
            ),
            File(
                name="opencode2.rpm",
                url="https://github.com/sst/opencode/releases/download/v1.0.164/opencode-desktop-linux-x86_64.rpm",
            ),
        ]
    )

    ghd.download_files(download_config)
    print(ghd.download_cache)
