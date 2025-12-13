# Agent Handbook (ublue-kinoite)

## What this repo is

This repository builds custom Fedora Atomic desktop images using **BlueBuild** recipes.

- BlueBuild recipes live in `recipes/`.
- Custom artifacts (DNF repo files, vendored RPMs, copied system files) live in `files/`.
- GitHub Actions builds/publishes images via `blue-build/github-action@v1` (`.github/workflows/build.yml`).

## Quick commands (authoritative)

Commands below are **observed in `justfile` / scripts**.

### Build images locally

Requires `bluebuild` and `just`.

- Kinoite: `just build-kinoite`
- Kinoite (NVIDIA): `just build-kinoite-nvidia`
- Aurora DX fork: `just build-aurora`
- Aurora DX (NVIDIA base): `just build-aurora-nvidia`

What the `just build-*` tasks do (`justfile:1-15`):

- `bluebuild generate ./recipes/<recipe>.yml -o Containerfile`
- `bluebuild build ./recipes/<recipe>.yml`

### Generate ISOs

Observed `just` targets (`justfile:17-21`):

- `just kinoite-iso` (uses image `ghcr.io/purkkis/kinoite:daily`)
- `just kinoite-nvidia-iso` (uses image `ghcr.io/purkkis/kinoite-nvidia:daily`)

### Build + upload ISOs to Backblaze B2

- `./build-isos.sh`

`build-isos.sh` requires (`build-isos.sh:8-33`):

- `bluebuild`
- `aws` CLI
- env vars: `B2_ENDPOINT`, `B2_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (see `.env.example`)

It currently builds/uploads only (`build-isos.sh:49-52`):

- `kinoite.iso` from `ghcr.io/purkkis/kinoite:daily`
- `kinoite-nvidia.iso` from `ghcr.io/purkkis/kinoite-nvidia:daily`

(Aurora ISO lines are present but commented out.)

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
  - `kinoite.yml`, `kinoite-nvidia.yml`, `aurora.yml`, `aurora-nvidia.yml`
  - shared fragments: `_*.yml` / `_*.yaml`
- `files/dnf/`: DNF `.repo` files and vendored RPMs referenced by the recipes
- `files/usr_bin/`: scripts copied into the image (via `recipes/_boot_to_windows.yml`)
- `files/usr_share_applications/`: `.desktop` files copied into the image
- `files/dropbox/`: Docker-based builder for Dropbox/nautilus-dropbox RPMs
- `.github/workflows/`: CI pipelines for building images and (manual) ISO publishing
- `docs/`: operational docs (e.g. remotes sync, automated ISO builds)

## BlueBuild recipe + module patterns

### Schemas

All recipe/module YAMLs include YAML language server schema headers:

- Recipes (`recipes/*.yml` like `recipes/kinoite.yml:1-2`):
  - `# yaml-language-server: $schema=https://schema.blue-build.org/recipe-v1.json`
- Module fragments (`recipes/_*.yml` like `recipes/_kinoite-dnf.yml:1-2`):
  - `# yaml-language-server: $schema=https://schema.blue-build.org/module-list-v1.json`

### Composition

Recipes primarily compose shared fragments via `from-file` (`recipes/kinoite.yml:12-17`, `recipes/aurora.yml:12-14`).

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
  - Installs `chatwise.rpm` from `files/dnf/chatwise.rpm` (`recipes/_kinoite-dnf.yml:23`).
  - Installs a Fedora-version-specific Dropbox RPM (`dropbox-v2025.05.20-f42.rpm`) (`recipes/_kinoite-dnf.yml:27`).
  - Enables `tailscaled.service` (`recipes/_kinoite-dnf.yml:51-54`).

- `recipes/_aurora-dnf.yml`
  - Similar structure, but uses `dropbox-v2025.05.20-f43.rpm` (`recipes/_aurora-dnf.yml:24`).
  - Demonstrates `remove` with `auto-remove: true` (`recipes/_aurora-dnf.yml:39-42`).

- `recipes/_chatwise-desktop-fix.yml`
  - `script` snippet that edits `/usr/share/applications/ChatWise.desktop` if present (`recipes/_chatwise-desktop-fix.yml:4-6`).

- `recipes/_kinoite-docker.yml`
  - Adds Docker CE repo via URL and installs Docker packages; enables `docker.service` (`recipes/_kinoite-docker.yml:4-18`).

- `recipes/_boot_to_windows.yml`
  - Copies `files/usr_bin/*` → `/usr/bin` and `files/usr_share_applications/*` → `/usr/share/applications` (`recipes/_boot_to_windows.yml:4-9`).

## Vendored artifacts (keep in sync)

### Chatwise RPM

- The recipes install `chatwise.rpm` from `files/dnf/chatwise.rpm`.
- CI downloads the latest RPM into `files/dnf/chatwise.rpm` before building (`.github/workflows/build.yml:29-35`).

Local builds: ensure `files/dnf/chatwise.rpm` exists (CI populates it; local builds won’t unless you provide it).

### Dropbox RPMs

- Dropbox RPMs live in `files/dnf/dropbox-v2025.05.20-f{41,42,43}.rpm`.
- The version tag is also set in `files/dropbox/justfile` as `docker_tag := "v2025.05.20"` (`files/dropbox/justfile:1`).

If updating Dropbox:

- Update `files/dropbox/justfile` (`docker_tag`), rebuild RPMs (via `./build-dropbox.sh ...` or `files/dropbox/justfile`), and update the referenced RPM filenames in the relevant DNF module(s):
  - `recipes/_kinoite-dnf.yml` uses `...-f42.rpm`
  - `recipes/_aurora-dnf.yml` uses `...-f43.rpm`

## CI (GitHub Actions)

### Image builds

- `.github/workflows/build.yml`
  - Scheduled nightly (`cron: "30 6 * * *"`) and manual dispatch.
  - Matrix builds currently include only:
    - `kinoite-nvidia.yml`
    - `kinoite.yml`
    (Aurora entries are present but commented out.)
  - Downloads Chatwise RPM before running BlueBuild.

### ISO build workflow

- `.github/workflows/build-iso.yml`
  - Manual dispatch only.
  - Installs BlueBuild using the upstream install script and runs `./build-isos.sh`.
  - Uses secrets for Backblaze B2 S3-compatible upload (`B2_ENDPOINT`, `B2_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).

## Operational gotchas (observed)

- **Aurora is present but not built by CI by default**: Aurora recipes exist (`recipes/aurora*.yml`), but CI matrix entries are commented out (`.github/workflows/build.yml:21-25`).
- **ISO generation targets/scripts only cover Kinoite variants right now**:
  - `justfile` provides `kinoite-iso` and `kinoite-nvidia-iso` only.
  - `build-isos.sh` has Aurora ISO calls commented out.
- **Docs vs script mismatch**: `docs/automated-iso-builds.md` states `build-isos.sh` uses `sudo`, but `build-isos.sh` currently invokes `bluebuild` directly.
- **Image naming mismatch across files**:
  - ISO generation uses `ghcr.io/purkkis/kinoite(:daily)` and `ghcr.io/purkkis/kinoite-nvidia(:daily)`.
  - `README.md` installation examples reference `ghcr.io/purkkis/ublue-kinoite:latest`.
  Keep these aligned when changing publish targets/tags.
- **boot-to-windows behavior**: `/usr/bin/boot-to-windows` calls `efibootmgr`, `kdialog`, and `sudo`, and the `.desktop` entry uses `pkexec` (`files/usr_bin/boot-to-windows:4-14`, `files/usr_share_applications/boot-to-windows.desktop:9`). Ensure required binaries/polkit expectations are satisfied by the base image.

## Git remotes

Operational notes for syncing GitHub/GitLab remotes are in `docs/syncing-remotes.md`.
