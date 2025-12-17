import requests
from typing import Optional, Dict, Any


REPOS = [
    "egoist/chatwise-releases",
    "dbeaver/dbeaver",
    "sst/opencode",
]


def get_latest_release(repo: str) -> Optional[Dict[str, Any]]:
    """Fetch the latest release information for a GitHub repository."""
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching latest release for {repo}: {e}")
        return None


def get_rpm_download_url(release_data: Dict[str, Any]) -> Optional[str]:
    """Extract the download URL for x86_64 RPM assets from release data."""
    try:
        assets = release_data.get("assets", [])
        for asset in assets:
            name = asset.get("name", "")
            if name.endswith("x86_64.rpm"):
                return asset.get("browser_download_url")
        return None
    except Exception as e:
        print(f"Error extracting RPM download URL: {e}")
        return None


def download_file(url: str, output_path: str) -> bool:
    """Download a file from URL to the specified output path."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False
