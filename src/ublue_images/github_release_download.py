import tempfile
from typing import Optional

import requests
from loguru import logger

from ublue_images.models.github import Model

REPOS = [
    "egoist/chatwise-releases",
    "dbeaver/dbeaver",
    "sst/opencode",
]


def get_latest_release(repo: str) -> Optional[Model]:
    """Fetch the latest release information for a GitHub repository."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return Model(**response.json())
    except requests.RequestException as e:
        logger.error(f"Error fetching latest release for {repo}: {e}")
        return None


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


def download_file_to_tmp_dir(url: str) -> str:
    """
    Downloads a file into a tmp directory, and returns the file path

    Args:
        url (str): The URL of the file to download

    Returns:
        str: The path to the downloaded file
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            response = requests.get(url)
            response.raise_for_status()
            tmp_file.write(response.content)
            tmp_file_path = tmp_file.name
        return tmp_file_path
    except requests.RequestException as e:
        logger.error(f"Error downloading file from {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating temporary file for {url}: {e}")
        raise


if __name__ == "__main__":
    r = download_file_to_tmp_dir(
        "https://github.com/sst/opencode/releases/download/v1.0.164/opencode-desktop-linux-x86_64.rpm"
    )
    print(r)
