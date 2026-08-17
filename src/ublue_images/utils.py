from pathlib import Path

import requests
from loguru import logger

REQUEST_TIMEOUT = (5, 60)
DOWNLOAD_CHUNK_SIZE = 1024 * 1024


def download_file(url: str, destination: Path) -> int:
    """
    Download a URL to disk and return the number of bytes written.

    Args:
        url: The URL to download
        destination: The path to save the file to

    Returns:
        The number of bytes written
    """
    bytes_written = 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=REQUEST_TIMEOUT) as response:
        response.raise_for_status()
        with destination.open("wb") as file_handle:
            for chunk in response.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                bytes_written += len(chunk)
                file_handle.write(chunk)
    logger.info(f"Downloaded {url} ({bytes_written} bytes) to {destination}")
    return bytes_written
