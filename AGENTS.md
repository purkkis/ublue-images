# Agents.md

## What this repo is

This repository builds custom Fedora Atomic desktop images using **BlueBuild** recipes.

- BlueBuild recipes live in `recipes/`.
- Custom artifacts (DNF repo files, vendored RPMs, copied system files) live in `files/`.
- GitHub Actions builds/publishes images via `blue-build/github-action@v1` (`.github/workflows/build.yml`).

## YAML files

List ordering in YAML files: keep list items in alphabetical order. If a list item is a URL, sort by the name of the downloaded file (not by the leading `https://...`).

## Quick commands (authoritative)

Commands below are **observed in `justfile` / scripts**.

### Build images locally

Requires `bluebuild` and `just`.

- Kinoite: `just build-kinoite`
- Kinoite (NVIDIA): `just build-kinoite-nvidia`

What the `just build-*` tasks do (`justfile:1-15`):

- `bluebuild generate ./recipes/<recipe>.yml -o Containerfile`
- `bluebuild build ./recipes/<recipe>.yml`

### Generate ISOs

Observed `just` targets (`justfile:17-24`):

- `just kinoite-iso` (uses image `ghcr.io/purkkis/kinoite:daily`)
- `just kinoite-nvidia-iso` (uses image `ghcr.io/purkkis/kinoite-nvidia:daily`)
- `just kinoite-nvidia-build-iso` (builds ISO from recipe `recipes/kinoite-nvidia.yml`)

### Build + upload ISOs to Backblaze B2

- `./build-isos.sh`

`build-isos.sh` requires (`build-isos.sh:8-33`):

- `bluebuild`
- `aws` CLI
- env vars: `B2_ENDPOINT`, `B2_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (see `.env.example`)

It currently builds/uploads only (`build-isos.sh:49-52`):

- `kinoite.iso` from `ghcr.io/purkkis/kinoite:daily`
- `kinoite-nvidia.iso` from `ghcr.io/purkkis/kinoite-nvidia:daily`

### Build vendored Dropbox RPMs

- `./build-dropbox.sh <fedora_version> [fedora_version ...]` (e.g. `./build-dropbox.sh 42 43`) (`build-dropbox.sh:22-26`)

This runs `just build <version>` inside `files/dropbox/` (`build-dropbox.sh:34-40`).

### Formatting checks

- `prek run --all-files` (`.pre-commit-config.yaml:1-12`)

Hooks enforced:

- trailing whitespace
- EOF newline
- YAML validity
- LF line endings (`mixed-line-ending --fix=lf`)

`files/dropbox/dropbox.patch` is excluded (`.pre-commit-config.yaml:3`).

## Repository layout

- `recipes/`: BlueBuild recipes and shared module fragments
  - `kinoite.yml`, `kinoite-nvidia.yml`
  - shared fragments: `_*.yml` / `_*.yaml`
- `files/dnf/`: DNF `.repo` files and vendored RPMs referenced by the recipes
- `files/usr_bin/`: scripts copied into the image (via `recipes/_boot_to_windows.yml`)
- `files/usr_share_applications/`: `.desktop` files copied into the image
- `files/dropbox/`: Docker-based builder for Dropbox/nautilus-dropbox RPMs
- `.github/workflows/`: CI pipelines for building images and (manual) ISO publishing

## BlueBuild recipe + module patterns

### Schemas

All recipe/module YAMLs include YAML language server schema headers:

- Recipes (`recipes/*.yml` like `recipes/kinoite.yml:1-2`):
  - `# yaml-language-server: $schema=https://schema.blue-build.org/recipe-v1.json`
- Module fragments (`recipes/_*.yml` like `recipes/_kinoite-dnf.yml:1-2`):
  - `# yaml-language-server: $schema=https://schema.blue-build.org/module-list-v1.json`

### Composition

Recipes primarily compose shared fragments via `from-file` (`recipes/kinoite.yml:12-17`).

Common module types used in this repo:

- `dnf` (repos + packages)
- `default-flatpaks`
- `fonts`
- `brew`
- `files`
- `systemd`
- `script`
- `akmods` (Kinoite NVIDIA recipe)
- `signing` (last module in each recipe)

### Notable modules

- `recipes/_kinoite-dnf.yml`
  - Adds `.repo` files from `files/dnf/` and installs packages.
  - Installs `chatwise.rpm` from `files/dnf/chatwise.rpm` (`recipes/_kinoite-dnf.yml:52`).
  - Installs `dbeaver.rpm` from `files/dnf/dbeaver.rpm` (`recipes/_kinoite-dnf.yml:53`).
  - Installs a Fedora-version-specific Dropbox RPM (`dropbox-v2025.05.20-f42.rpm`) (`recipes/_kinoite-dnf.yml:54`).
  - Installs `opencode.rpm` from `files/dnf/opencode.rpm` (`recipes/_kinoite-dnf.yml:55`).
  - Installs Positron and Protonmail Bridge via direct URLs (`recipes/_kinoite-dnf.yml:56-57`).
  - Enables `tailscaled.service` (`recipes/_kinoite-dnf.yml:59-62`).

- `recipes/_desktop-file-fixes.yml`
  - `script` snippets that edit desktop files to fix Electron app issues:
    - `/usr/share/applications/ChatWise.desktop` - adds `WEBKIT_DISABLE_COMPOSITING_MODE=1 GDK_BACKEND="x11"` (`recipes/_desktop-file-fixes.yml:6`).
    - `/usr/share/applications/OpenCode.desktop` - adds same environment variables (`recipes/_desktop-file-fixes.yml:7`).

- `recipes/_kinoite-docker.yml`
  - Adds Docker CE repo via URL and installs Docker packages; enables `docker.service` (`recipes/_kinoite-docker.yml:4-18`).

- `recipes/_boot_to_windows.yml`
  - Copies `files/usr_bin/*` → `/usr/bin` and `files/usr_share_applications/*` → `/usr/share/applications` (`recipes/_boot_to_windows.yml:4-9`).

## Vendored artifacts (keep in sync)

### Chatwise, DBeaver & OpenCode RPMs

- The recipes install `chatwise.rpm`, `dbeaver.rpm`, and `opencode.rpm` from `files/dnf/`.
- CI downloads the latest RPMs into `files/dnf/` before building (`.github/workflows/build.yml:28-47`).

Local builds: ensure these RPMs exist in `files/dnf/` (CI populates them; local builds won’t unless you provide them).

### Dropbox RPMs

- Dropbox RPMs live in `files/dnf/dropbox-v2025.05.20-f{42,43}.rpm`.
- The version tag is also set in `files/dropbox/justfile` as `docker_tag := "v2025.05.20"` (`files/dropbox/justfile:1`).

If updating Dropbox:

- Update `files/dropbox/justfile` (`docker_tag`), rebuild RPMs (via `./build-dropbox.sh ...` or `files/dropbox/justfile`), and update the referenced RPM filenames in the relevant DNF module(s):
  - `recipes/_kinoite-dnf.yml` uses `...-f42.rpm` (`recipes/_kinoite-dnf.yml:54`)

## CI (GitHub Actions)

### Image builds

- `.github/workflows/build.yml`
  - Scheduled nightly (`cron: "30 6 * * *"`) and manual dispatch.
  - Runs on `ubicloud-standard-4` (not `ubuntu-latest`).
  - Matrix builds currently include only:
    - `kinoite-nvidia.yml`
    - `kinoite.yml`
  - Downloads Chatwise, DBeaver, and OpenCode RPMs before running BlueBuild.
  - Uses `actions/checkout@v6`.

### ISO build workflow

- `.github/workflows/build-iso.yml`
  - Runs weekly (Monday 01:00 UTC) and manual dispatch.
  - Runs on `ubicloud-standard-4`.
  - Installs BlueBuild using the upstream install script and runs `./build-isos.sh`.
  - Uses secrets for Backblaze B2 S3-compatible upload (`B2_ENDPOINT`, `B2_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

## Operational gotchas (observed)

- **ISO generation targets/scripts only cover Kinoite variants right now**:
  - `justfile` provides `kinoite-iso` and `kinoite-nvidia-iso` only.
- **Image naming mismatch across files**:
  - ISO generation uses `ghcr.io/purkkis/kinoite(:daily)` and `ghcr.io/purkkis/kinoite-nvidia(:daily)`.
  - `README.md` installation examples reference `ghcr.io/purkkis/kinoite`.
    Keep these aligned when changing publish targets/tags.
- **boot-to-windows behavior**: `/usr/bin/boot-to-windows` calls `efibootmgr`, `kdialog`, and `sudo`, and the `.desktop` entry uses `pkexec` (`files/usr_bin/boot-to-windows:4-14`, `files/usr_share_applications/boot-to-windows.desktop:9`). Ensure required binaries/polkit expectations are satisfied by the base image.
