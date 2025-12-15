import argparse
import json
import os
from pathlib import Path
from typing import Iterable

import requests
from pydantic import BaseModel, Field, HttpUrl


class PinnedRpm(BaseModel):
    url: HttpUrl
    filename: str
    cache_key: str


class LatestRpm(BaseModel):
    github_owner: str
    github_repo: str
    filename: str


class RpmConfig(BaseModel):
    pinned: list[PinnedRpm] = Field(default_factory=list)
    latest: list[LatestRpm] = Field(default_factory=list)


def _download_file(url: str, dest: Path) -> None:
    """Download a file from a URL to a destination path.

    Downloads to a temporary file first, then atomically moves it to the
    destination to avoid partial downloads.

    Args:
        url: URL to download from.
        dest: Destination path for the downloaded file.

    Raises:
        requests.HTTPError: If the download fails.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)

    tmp = dest.with_suffix(dest.suffix + ".partial")
    if tmp.exists():
        tmp.unlink()

    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    os.replace(tmp, dest)


def _github_latest_release(owner: str, repo: str) -> dict:
    """Fetch the latest release information from a GitHub repository.

    Args:
        owner: GitHub repository owner.
        repo: GitHub repository name.

    Returns:
        Dictionary containing the release information from GitHub API.

    Raises:
        requests.HTTPError: If the API request fails.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    r = requests.get(
        url,
        headers={"Accept": "application/vnd.github+json"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def _find_rpm_asset_url(release: dict) -> str:
    """Find the x86_64 RPM asset URL in a GitHub release.

    Args:
        release: GitHub release dictionary from the API.

    Returns:
        Browser download URL for the x86_64 RPM asset.

    Raises:
        RuntimeError: If no x86_64 RPM asset is found.
    """
    assets = release.get("assets") or []
    for asset in assets:
        name = asset.get("name") or ""
        if name.endswith("x86_64.rpm"):
            url = asset.get("browser_download_url")
            if url:
                return url
    raise RuntimeError("No x86_64.rpm asset found in latest release")


def _should_skip(dest: Path) -> bool:
    """Check if a file already exists and should be skipped.

    Args:
        dest: Path to check.

    Returns:
        True if the file exists and has non-zero size, False otherwise.
    """
    return dest.exists() and dest.stat().st_size > 0


def _print_outputs(lines: Iterable[str], github_output: str | None) -> None:
    """Print output lines to stdout or GitHub Actions output file.

    Args:
        lines: Lines to output.
        github_output: Path to GitHub Actions output file, or None to print to stdout.
    """
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        return

    for line in lines:
        print(line)


def _load_config(config_path: Path) -> RpmConfig:
    """Load and validate RPM configuration from a JSON file.

    Args:
        config_path: Path to the JSON configuration file.

    Returns:
        Validated RpmConfig object.

    Raises:
        pydantic.ValidationError: If the configuration is invalid.
        FileNotFoundError: If the configuration file doesn't exist.
    """
    with open(config_path, encoding="utf-8") as f:
        data = json.load(f)
    return RpmConfig.model_validate(data)


def cmd_cache_info(args: argparse.Namespace) -> int:
    """Generate cache paths and key for GitHub Actions caching.

    Queries GitHub API for latest release tags and generates a cache key
    that includes all RPM versions.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    config = _load_config(Path(args.config))
    dnf_dir = Path(args.dnf_dir)

    paths = []
    cache_keys = []

    for item in config.pinned:
        paths.append(str(dnf_dir / item.filename))
        cache_keys.append(item.cache_key)

    for item in config.latest:
        release = _github_latest_release(item.github_owner, item.github_repo)
        tag = release.get("tag_name", "")
        paths.append(str(dnf_dir / item.filename))
        cache_keys.append(f"{item.github_repo}-{tag}")

    lines = [
        "paths<<EOF",
        *paths,
        "EOF",
        f"key=rpms-{'-'.join(cache_keys)}",
    ]
    _print_outputs(lines, args.github_output)
    return 0


def cmd_download(args: argparse.Namespace) -> int:
    """Download all configured RPM packages.

    Downloads pinned RPMs from direct URLs and latest RPMs from GitHub releases.
    Skips files that already exist with non-zero size.

    Args:
        args: Parsed command-line arguments.

    Returns:
        Exit code (0 for success).
    """
    config = _load_config(Path(args.config))
    dnf_dir = Path(args.dnf_dir)

    for item in config.pinned:
        dest = dnf_dir / item.filename
        if _should_skip(dest):
            continue
        _download_file(str(item.url), dest)

    for item in config.latest:
        dest = dnf_dir / item.filename
        if _should_skip(dest):
            continue
        release = _github_latest_release(item.github_owner, item.github_repo)
        asset_url = _find_rpm_asset_url(release)
        _download_file(asset_url, dest)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_cache = sub.add_parser("cache-info")
    p_cache.add_argument("--config", default="scripts/rpms.json")
    p_cache.add_argument("--dnf-dir", default="files/dnf")
    p_cache.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    p_cache.set_defaults(func=cmd_cache_info)  # pass args to cmd_cache_info function

    p_dl = sub.add_parser("download")
    p_dl.add_argument("--config", default="scripts/rpms.json")
    p_dl.add_argument("--dnf-dir", default="files/dnf")
    p_dl.set_defaults(func=cmd_download)  # pass args to cmd_download function

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        print("=== Sample GitHub Actions Output Demo ===\n")
        print("1. Running: cache-info command\n")
        print("Output that would be written to $GITHUB_OUTPUT:\n")

        sys.argv = ["download_rpms.py", "cache-info"]
        try:
            main()
        except SystemExit:
            pass

        print("\n" + "=" * 50)
        print("\nThese outputs are used in .github/workflows/build.yml:")
        print("  path: ${{ steps.rpm-cache-info.outputs.paths }}")
        print("  key: ${{ steps.rpm-cache-info.outputs.key }}")

        print("\n" + "=" * 50)
        print("\n2. Running: download command (to ./tmp folder)\n")

        sys.argv = ["download_rpms.py", "download", "--dnf-dir", "./tmp"]
        try:
            main()
        except SystemExit:
            pass

        print("\nDownload complete! Check ./tmp folder for downloaded RPMs.")
    else:
        raise SystemExit(main())
