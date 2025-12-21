import os
import tempfile
from pathlib import Path

import awswrangler as wr
import requests
from dotenv import load_dotenv
from joblib import Memory, expires_after
from loguru import logger
from pydantic import BaseModel, Field

from ublue_images.models.github import GithubReleases

load_dotenv()

MEMORY = Memory(Path("./tmp"), verbose=0)
B2_BUCKET = os.getenv("B2_BUCKET_NAME")
B2_ENDPOINT = os.getenv("B2_ENDPOINT")

if not B2_ENDPOINT:
    raise ValueError("B2_ENDPOINT not set!")

os.environ["AWS_ENDPOINT_URL"] = B2_ENDPOINT


class File(BaseModel):
    name: str
    version: str
    url: str


class DownloadFiles(BaseModel):
    files: list[File] = Field(default_factory=list)


class GitHubReleaseDownloader:
    download_cache: DownloadFiles

    def __init__(self):
        self.download_cache = DownloadFiles()

    @staticmethod
    def get_latest_release(repo: str) -> GithubReleases:
        """Fetch the latest release information for a GitHub repository."""
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        try:
            response = requests.get(url)
            response.raise_for_status()
            return GithubReleases.model_validate_json(response.json())
        except Exception as e:
            logger.error(f"Error fetching latest release for {repo}: {e}")
            raise e

    @staticmethod
    def get_rpm_download_url(release_data: GithubReleases) -> str:
        """Extract the download URL for x86_64 RPM assets from release data."""
        try:
            for asset in release_data.assets:
                if asset.name.endswith("x86_64.rpm"):
                    return asset.browser_download_url
            raise ValueError("No x86_64 RPM asset found")
        except Exception as e:
            logger.error(f"Error extracting RPM download URL: {e}")
            raise e

    @staticmethod
    @MEMORY.cache(cache_validation_callback=expires_after(days=1))
    def _download(url: str, file: str):
        logger.info(f"Downloading {file}...")
        response = requests.get(url)
        response.raise_for_status()
        return response.content

    def download_file_to_tmp_dir(self, file_config: File):
        """
        Downloads a file into a tmp directory, and returns the file path

        Args:
            url (str): The URL of the file to download

        Returns:
            str: The path to the downloaded file
        """
        try:
            with tempfile.NamedTemporaryFile() as tmp_file:
                content = self._download(file_config.url, file_config.name)
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
                s3_path = f"s3://{B2_BUCKET}/bluebuild-files/{file_config.name}"
                wr.s3.upload(local_file=tmp_file_path, path=s3_path)
            self.download_cache.files.append(
                File(name=file_config.name, url=s3_path, version=file_config.version)
            )
        except requests.RequestException as e:
            logger.error(f"Error downloading file from {file_config.url}: {e}")
            raise e
        except Exception as e:
            logger.error(f"Error creating temporary file for {file_config.url}: {e}")
            raise e

    def download_files(self, config: DownloadFiles):
        for file_config in config.files:
            self.download_file_to_tmp_dir(file_config)


if __name__ == "__main__":
    ghd = GitHubReleaseDownloader()

    # Example usage
    download_config = DownloadFiles(
        files=[
            File(
                name="opencode.rpm",
                url="https://github.com/sst/opencode/releases/download/v1.0.164/opencode-desktop-linux-x86_64.rpm",
                version="1.0.164",
            ),
            File(
                name="opencode2.rpm",
                url="https://github.com/sst/opencode/releases/download/v1.0.164/opencode-desktop-linux-x86_64.rpm",
                version="1.0.164",
            ),
        ]
    )

    ghd.download_files(download_config)
    print(ghd.download_cache)
