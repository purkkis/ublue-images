# Custom Fedora Atomic Images

## Overview

This repository builds custom Fedora Atomic desktop images using **BlueBuild** recipes. These are immutable, atomic operating system images based on Fedora Kinoite (KDE Plasma) with additional software and configuration.

- **Recipes**: `recipes/` (kinoite-nvidia.yml and shared fragments)
- **Artifacts**: `files/` (DNF repo files, RPMs, scripts, sysusers configs)
- **Builds**: GitHub Actions via `blue-build/github-action@v1`

## Code Organization

```
├── recipes/                 # BlueBuild recipes and shared modules
├── files/                   # Vendored artifacts and configs
│   ├── dnf/                 # DNF repos and RPMs
│   │   ├── *.repo           # Repository configuration files
│   │   ├── rpms/            # Hardcoded RPM versions (from files.json)
│   │   ├── tags/            # Tagged release RPMs (from tags.json)
│   │   └── *.rpm            # Versioned RPMs (e.g., dropbox)
│   ├── usr_lib_sysusers_d/  # System user/group configurations
│   └── dropbox/             # Dropbox build files
├── src/ublue_images/        # Python scripts for RPM management
├── .github/workflows/       # CI/CD pipelines
└── *.sh                     # Build scripts
```

## YAML Files

List ordering in YAML files: keep list items in alphabetical order. If a list item is a URL, sort by the name of the downloaded file (not by the leading `https://...`).

## Quick Commands

Requires `bluebuild` and `just`:

- **Build Kinoite (NVIDIA)**: `just build-image-kinoite-nvidia`
- **Generate ISOs**:
  - `just build-iso-kinoite-from-ghcr-image`
  - `just build-iso-kinoite-nvidia-from-ghcr-image`
  - `just build-iso-kinoite-nvidia-from-recipe`

## Repository Structure

- `.env.example`, `.envrc`: Environment configuration examples
- `.github/workflows/`: CI/CD pipelines
- `.pre-commit-config.yaml`: Pre-commit hook configuration
- `.python-version`: Python version specification
- `build-dropbox.sh`, `build-isos.sh`: Build scripts
- `cosign.pub`: Public key for image verification
- `justfile`: Command definitions for the `just` command runner
- `pyproject.toml`, `uv.lock`: Python project configuration
- `recipes/`: BlueBuild recipes and shared modules (prefixed with `_`)
  - `kinoite.yml`: Base Kinoite image recipe (Fedora 43)
  - `kinoite-nvidia.yml`: Kinoite image with NVIDIA drivers (Fedora 42)
- `files/dnf/`: DNF repos and vendored RPMs (chatwise, dbeaver, opencode, dropbox)
- `files/usr_lib_sysusers_d/`: System user/group configs
- `src/ublue_images/`: Python scripts for downloading RPMs from GitHub
- `files/dropbox/`: Dropbox build files and Dockerfile

## Key Modules

- `_amd-rocm.yml`: Enables RPM Fusion repositories (used in kinoite.yml)
- `_common-flatpaks.yml`: Installs common Flatpak applications
- `_kinoite-docker.yml`: Installs Docker CE components
- `_kinoite-dnf.yml`: Installs packages from repos, local RPMs, and URLs; enables tailscaled
- `_kinoite-fonts.yaml`: Installs Nerd Fonts and Google Fonts
- `_scripts.yml`: Fixes desktop files for Electron apps
- `_sysusers.yml`: Creates system users/groups via systemd-sysusers

## Recipe Differences

The repository provides two main image recipes:

1. **kinoite.yml** - Base Kinoite image:
   - Fedora version: 43
   - AMD GPU support via `_amd-rocm.yml` module
   - No proprietary drivers included

2. **kinoite-nvidia.yml** - NVIDIA-optimized Kinoite image:
   - Fedora version: 42
   - NVIDIA driver support via akmods module with `nvidia-open` driver
   - Includes Steam from negativo17 repository
   - Uses older Fedora version for better NVIDIA driver compatibility

## Vendored Artifacts

Three types of vendored RPMs:

1. **Hardcoded versions**: Defined in `src/ublue_images/files.json` (e.g., Bitwarden, Positron) - downloaded to `files/dnf/rpms/`
2. **Tagged releases**: Defined in `src/ublue_images/tags.json` (e.g., ChatWise, DBeaver) - downloaded to `files/dnf/tags/`
3. **Versioned RPMs**: Directly versioned files like `dropbox-f42.rpm` and `dropbox-f43.rpm` in `files/dnf/`

### Updating Vendored Artifacts

- **Hardcoded RPMs**: Update `src/ublue_images/files.json` and run `uv run src/ublue_images/rpms.py`
- **Tagged releases**: Run `uv run src/ublue_images/tags.py --refresh` to update tags, then `uv run src/ublue_images/tags.py --download` to download
- **Dropbox RPMs**: Modify `files/dropbox/justfile` and rebuild with `./build-dropbox.sh`

## Build Process

### Image Builds (.github/workflows/build.yml)

- **Nightly builds**: Run at 06:30 UTC on ubicloud-standard-4 instances
- **Manual builds**: Can be triggered via GitHub Actions UI
- **RPM Management**: Automatically downloads latest RPMs before BlueBuild using Python scripts
- **Caching**: Caches downloaded RPMs based on files.json/tags.json hashes to speed up builds
- **Cleanup**: Automatically deletes package versions older than 1 day to save space
- **Signing**: Images are signed with Sigstore cosign for verification

### ISO Builds (.github/workflows/build-iso.yml)

- **Weekly builds**: Automated ISO generation
- **Manual builds**: Can be triggered via GitHub Actions UI
- **Upload**: ISOs are uploaded to Backblaze B2 storage
- **Process**: Runs `./build-isos.sh` with required environment variables

## System Users

Creates system groups via systemd-sysusers:

- `onepassword` (ID 1500) for app access to browser integration
- `onepassword-cli` (ID 1600) for CLI access

Configs in `files/usr_lib_sysusers_d/` applied by `_sysusers.yml`.

## Development Workflow

1. **Install dependencies**: `bluebuild` CLI, `just` runner, and `uv` for Python package management
2. **Build images**:
   - `just build-image-kinoite-nvidia` for NVIDIA variant
3. **Generate ISOs**:
   - `just build-iso-kinoite-from-ghcr-image` to build from pre-built image
   - `just build-iso-kinoite-nvidia-from-recipe` to build from recipe

## Security

- **Image signing**: All images are signed with Sigstore cosign for verification
- **Trusted sources**: Only uses trusted repositories and verified packages
- **Verification**: Users can verify images with `cosign verify --key cosign.pub ghcr.io/purkkis/kinoite`

## Python Scripts for RPM Management

The `src/ublue_images/` directory contains Python scripts that manage RPM downloads:

- `files.json`: Defines hardcoded RPMs with specific versions that rarely change
- `tags.json`: Defines RPMs that should always use the latest GitHub release tag
- `rpms.py`: Downloads RPMs defined in files.json to `files/dnf/rpms/`
- `tags.py`:
  - With `--refresh`: Updates tags.json with latest GitHub release tags
  - With `--download`: Downloads RPMs defined in tags.json to `files/dnf/tags/`

These scripts are automatically run by the CI workflow before building images to ensure the latest software versions.
