# Custom Fedora Atomic Images

## Overview

This repository builds custom Fedora Atomic desktop images using **BlueBuild** recipes.

- Recipes: `recipes/` (kinoite.yml, kinoite-nvidia.yml, and shared fragments)
- Artifacts: `files/` (DNF repo files, RPMs, scripts, sysusers configs)
- Builds: GitHub Actions via `blue-build/github-action@v1`

## YAML Files

List ordering in YAML files: keep list items in alphabetical order. If a list item is a URL, sort by the name of the downloaded file (not by the leading `https://...`).

## Quick Commands

Requires `bluebuild` and `just`:

- Build Kinoite: `just build-image-kinoite`
- Build Kinoite (NVIDIA): `just build-image-kinoite-nvidia`
- Generate ISOs: `just build-iso-kinoite-from-ghcr-image`

## Repository Structure

- `recipes/`: BlueBuild recipes and shared modules (prefixed with `_`)
- `files/dnf/`: DNF repos and vendored RPMs (chatwise, dbeaver, opencode, dropbox)
- `files/usr_bin/`: Scripts copied to /usr/bin
- `files/usr_lib_sysusers_d/`: System user/group configs
- `.github/workflows/`: CI/CD pipelines
- `src/ublue_images/`: Python scripts for downloading RPMs from GitHub

## Recipes and Modules

Main recipes compose shared fragments via `from-file`:

- `kinoite.yml` and `kinoite-nvidia.yml` (NVIDIA adds akmods)
- Common modules: dnf, default-flatpaks, fonts, brew, files, systemd, script, signing

### Key Modules

- `_kinoite-dnf.yml`: Installs packages from repos, local RPMs, and URLs; enables tailscaled
- `_boot_to_windows.yml`: Copies scripts and desktop files
- `_scripts.yml`: Fixes Electron apps and 1Password permissions
- `_sysusers.yml`: Creates system users/groups via systemd-sysusers

## Vendored Artifacts

Two types of vendored RPMs:
1. Hardcoded versions in `src/ublue_images/files.json` (e.g., Bitwarden, Positron)
2. Tagged releases in `src/ublue_images/tags.json` (e.g., ChatWise, DBeaver)

Both downloaded by CI to `files/dnf/rpms/` and `files/dnf/tags/` respectively before builds.

- Dropbox RPMs: Versioned files (`dropbox-v2025.05.20-f{42,43}.rpm`) in `files/dnf/`
- To update Dropbox: Modify `files/dropbox/justfile` and rebuild with `./build-dropbox.sh`

## CI/CD

### Image Builds (.github/workflows/build.yml)
- Nightly + manual builds on ubicloud-standard-4
- Builds both kinoite variants
- Downloads latest RPMs before BlueBuild using Python scripts in `src/ublue_images/`
- Caches downloaded RPMs based on files.json/tags.json hashes
- Signs images with cosign

### ISO Builds (.github/workflows/build-iso.yml)
- Weekly + manual builds
- Runs `./build-isos.sh` with Backblaze B2 upload

## System Users

Creates system groups via systemd-sysusers:
- `onepassword` (ID 1500) for app access
- `onepassword-cli` (ID 1600) for CLI access

Configs in `files/usr_lib_sysusers_d/` applied by `_sysusers.yml`.

## Development Workflow

1. Install: `bluebuild` CLI, `just` runner
2. Build images: `just build-image-kinoite*` commands
3. Generate ISOs: `just build-iso-kinoite*` commands

## Security

- Images signed with Sigstore cosign
- Only trusted repos and verified packages

## Python Scripts for RPM Management

The `src/ublue_images/` directory contains Python scripts that manage RPM downloads:

- `files.json`: Defines hardcoded RPMs with specific versions
- `tags.json`: Defines RPMs that should always use the latest GitHub release tag
- `rpms.py`: Downloads RPMs defined in files.json to `files/dnf/rpms/`
- `tags.py`:
  - With `--refresh`: Updates tags.json with latest GitHub release tags
  - With `--download`: Downloads RPMs defined in tags.json to `files/dnf/tags/`

These scripts are automatically run by the CI workflow before building images.
