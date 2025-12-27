# Custom Fedora Atomic Images

## Overview

This repository builds custom Fedora Atomic desktop images using **BlueBuild** recipes. These are immutable, atomic operating system images based on Fedora Kinoite (KDE Plasma) with additional software and configuration.

- **Recipes**: `recipes/` (kinoite.yml, kinoite-nvidia.yml, and shared fragments)
- **Artifacts**: `files/` (DNF repo files, RPMs, scripts, sysusers configs)
- **Builds**: GitHub Actions via `blue-build/github-action@v1`

## YAML Files

List ordering in YAML files: keep list items in alphabetical order. If a list item is a URL, sort by the name of the downloaded file (not by the leading `https://...`).

## Quick Commands

Requires `bluebuild` and `just`:

- **Build Kinoite**: `just build-image-kinoite`
- **Build Kinoite (NVIDIA)**: `just build-image-kinoite-nvidia`
- **Generate ISOs**:
  - `just build-iso-kinoite-from-ghcr-image`
  - `just build-iso-kinoite-nvidia-from-ghcr-image`
  - `just build-iso-kinoite-nvidia-from-recipe`

## Repository Structure

- `recipes/`: BlueBuild recipes and shared modules (prefixed with `_`)
- `files/dnf/`: DNF repos and vendored RPMs (chatwise, dbeaver, opencode, dropbox)
- `files/usr_lib_sysusers_d/`: System user/group configs
- `.github/workflows/`: CI/CD pipelines
- `src/ublue_images/`: Python scripts for downloading RPMs from GitHub
- `files/dropbox/`: Dropbox build files and Dockerfile

## Recipes and Modules

Main recipes compose shared fragments via `from-file`:

- `kinoite.yml` and `kinoite-nvidia.yml` (NVIDIA adds akmods)
- Common modules: dnf, default-flatpaks, fonts, brew, files, systemd, script, signing

### Key Modules

- `_kinoite-dnf.yml`: Installs packages from repos, local RPMs, and URLs; enables tailscaled
- `_scripts.yml`: Fixes Electron apps and 1Password permissions
- `_sysusers.yml`: Creates system users/groups via systemd-sysusers
- `_common-brew.yml`: Installs Homebrew
- `_common-flatpaks.yml`: Installs common Flatpak applications
- `_kinoite-docker.yml`: Installs Docker-related packages
- `_kinoite-fonts.yaml`: Installs additional fonts

## Vendored Artifacts

Three types of vendored RPMs:
1. **Hardcoded versions**: Defined in `src/ublue_images/files.json` (e.g., Bitwarden, Positron) - downloaded to `files/dnf/rpms/`
2. **Tagged releases**: Defined in `src/ublue_images/tags.json` (e.g., ChatWise, DBeaver) - downloaded to `files/dnf/tags/`
3. **Versioned RPMs**: Directly versioned files like `dropbox-v2025.05.20-f{42,43}.rpm` in `files/dnf/`

### Updating Vendored Artifacts

- **Hardcoded RPMs**: Update `src/ublue_images/files.json` and run `uv run src/ublue_images/rpms.py`
- **Tagged releases**: Run `uv run src/ublue_images/tags.py --refresh` to update tags, then `uv run src/ublue_images/tags.py --download` to download
- **Dropbox RPMs**: Modify `files/dropbox/justfile` and rebuild with `./build-dropbox.sh`

## CI/CD

### Image Builds (.github/workflows/build.yml)
- **Nightly builds**: Run at 06:30 UTC on ubicloud-standard-4 instances
- **Manual builds**: Can be triggered via GitHub Actions UI
- **Builds both variants**: Standard Kinoite and NVIDIA-optimized variant
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
   - `just build-image-kinoite` for standard variant
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

## Important Gotchas

1. **1Password Groups**: After first installation, users must manually adjust group IDs:
   ```bash
   sudo groupmod -g 1500 onepassword
   sudo groupmod -g 1600 onepassword-cli
   ```

2. **Sublime Text Repositories**: Currently disabled due to upstream issues with the repository

3. **Build Requirements**: Building locally requires significant disk space and the `bluebuild` tool

4. **RPM Caching**: CI uses GitHub Actions caching to avoid re-downloading RPMs unnecessarily

5. **Image Cleanup**: Old container images are automatically deleted after 1 day to save storage

## Package Management Approach

This project uses a hybrid approach:
1. **DNF Repositories**: Standard packages from official repositories
2. **Vendored RPMs**: Manually downloaded packages that aren't available in repositories
3. **Flatpaks**: Applications distributed as Flatpaks for sandboxing
4. **Homebrew**: Additional package manager for user-space applications

This approach provides maximum flexibility while maintaining system stability and security.
