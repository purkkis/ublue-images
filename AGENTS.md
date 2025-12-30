# ublue-images (Custom Fedora Atomic Images)

## What this repo is

This repository builds custom Fedora Atomic desktop images (Fedora Kinoite) using **BlueBuild** recipes.

- **BlueBuild recipes** live in `recipes/`
- **Vendored artifacts/configs** live in `files/` (DNF repo files, RPMs, sysusers configs)
- **RPM management scripts** live in `src/ublue_images/` (Python)
- **CI** builds images + updates release tags via GitHub Actions in `.github/workflows/`

## Repository layout (high-signal)

```
recipes/                      BlueBuild recipes + shared modules (prefixed with `_`)
  kinoite.yml                 Base image recipe (image-version: 43)
  kinoite-nvidia.yml          NVIDIA variant recipe (image-version: 43)
  _kinoite-dnf.yml            DNF repos + packages + local/tagged RPM installs
  _common-flatpaks.yml        Flatpaks installed system-wide
  _sysusers.yml               systemd-sysusers setup (copies sysusers.d files)
  _scripts.yml                Post-install tweaks (desktop file edits)
  _amd-rocm.yml               RPMFusion + AMD/ROCm packages (used by kinoite.yml)
  _kinoite-docker.yml         Docker repo + docker packages + enable docker.service
  _kinoite-fonts.yaml         Nerd Fonts + Google fonts

files/
  dnf/                        DNF repo files and RPMs used by recipes
    *.repo                    Repo configuration consumed by recipes/_kinoite-dnf.yml
    dropbox-f43.rpm           Locally built RPM (see files/dropbox/)
    rpms/                     “Hardcoded/managed” RPMs (see src/ublue_images/files.json)
    tags/                     “Latest GitHub release tag” RPMs (see src/ublue_images/tags.json)
  usr_lib_sysusers_d/         sysusers.d entries copied into /usr/lib/sysusers.d
  dropbox/                    Docker-based build context + justfile to produce dropbox RPMs

src/ublue_images/
  github_release_download.py  GitHub release/tag lookup + download helpers
  rpms.py                     Download RPMs from src/ublue_images/files.json → files/dnf/rpms/
  tags.py                     Refresh tags.json and download tagged RPMs → files/dnf/tags/
  models/github.py            Pydantic model generated via datamodel-codegen

.github/workflows/
  build.yml                   Nightly image builds + auto-update tags.json
  build-iso.yml               Weekly ISO builds + upload to B2 (runs build-isos.sh)
```

## Essential commands

### BlueBuild / images (local)

Commands are defined in the top-level `justfile`:

- Build images:
  - `just build-image-kinoite`
  - `just build-image-kinoite-nvidia`

- Generate ISOs from pre-built images in GHCR:
  - `just build-iso-kinoite-from-ghcr-image`
  - `just build-iso-kinoite-nvidia-from-ghcr-image`

### RPM management (local / CI)

- Refresh GitHub release tags in `src/ublue_images/tags.json`:
  - `uv run src/ublue_images/tags.py --refresh`
  - (wrapper) `just update-github-release-tags`

- Download tagged-release RPMs into `files/dnf/tags/`:
  - `uv run src/ublue_images/tags.py --download`

- Download “hardcoded” RPMs into `files/dnf/rpms/`:
  - `uv run src/ublue_images/rpms.py`

### Dropbox RPM builds

- Build dropbox RPMs (expects `just` and `docker`):
  - `./build-dropbox.sh 42 43`

Under the hood this runs `files/dropbox/justfile` targets and writes into `files/dnf/dropbox-f<version>.rpm`.

### ISO build/upload script

- `./build-isos.sh <iso_name> <image>`

This script requires:
- `bluebuild` available on PATH
- `aws` CLI available on PATH
- Env vars: `B2_ENDPOINT`, `B2_BUCKET_NAME`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (see `.env.example`)

## CI workflows (what runs where)

### `.github/workflows/build.yml`

- Job `update-tags` runs `uv run src/ublue_images/tags.py --refresh` and auto-commits updates to `src/ublue_images/tags.json`.
- Job `bluebuild` runs on `ubicloud-standard-4` and builds a matrix of recipes:
  - `kinoite.yml`
  - `kinoite-nvidia.yml`
- CI caches `files/dnf/rpms` keyed by `src/ublue_images/files.json` and caches `files/dnf/tags` keyed by `src/ublue_images/tags.json`.

### `.github/workflows/build-iso.yml`

- Weekly ISO builds on `ubicloud-standard-4`.
- Installs `bluebuild` in CI (via an install script) and calls `./build-isos.sh`.

## Code conventions & style

### Python

- Python project metadata: `pyproject.toml`
- Supported Python: `>=3.11,<4.0` (`pyproject.toml:6`)
- Formatting/linting configuration:
  - Ruff `line-length = 100` and `indent-width = 4` (`pyproject.toml:25-27`)

There is no dedicated unit test suite in this repository; validation is primarily via pre-commit hooks and CI builds.

### Pre-commit

`.pre-commit-config.yaml` configures:
- whitespace/yaml/json/toml hygiene
- `ruff-check` (imports: `--select I --fix`)
- `ruff-format`
- `gitleaks`

## BlueBuild recipe patterns

- Recipes reference shared module fragments via `from-file: _something.yml`.
- Module lists include a `$schema` header.
- Lists in recipe YAML are typically kept in alphabetical order (repos, packages, flatpaks). Maintain the existing ordering when editing.

Key behavior in this repo:
- `recipes/_sysusers.yml` copies `files/usr_lib_sysusers_d/*` into `/usr/lib/sysusers.d` and runs `systemd-sysusers`.
- `recipes/_scripts.yml` uses `sed -i` snippets to patch `.desktop` Exec lines for certain Electron apps.
- `recipes/_kinoite-dnf.yml` installs:
  - packages from repo `.repo` files under `files/dnf/`
  - local RPMs under `files/dnf/` (e.g. `dropbox-f43.rpm`)
  - downloaded RPMs under `files/dnf/rpms/` and `files/dnf/tags/`

## Vendored RPM workflow (important)

There are two automation paths for RPMs:

1. **Hardcoded list**: `src/ublue_images/files.json` → downloaded by `src/ublue_images/rpms.py` into `files/dnf/rpms/`.
2. **Latest-tag list**: `src/ublue_images/tags.json` → refreshed by `src/ublue_images/tags.py --refresh` and downloaded by `--download` into `files/dnf/tags/`.

### Gotcha: download scripts delete output directories

`GitHubReleaseDownloader.download_files()` (used by both `rpms.py` and `tags.py --download`) removes and recreates the output directory (`src/ublue_images/github_release_download.py:127-134`).

Implications:
- Running `uv run src/ublue_images/rpms.py` will delete `files/dnf/rpms/` and then repopulate it *only* from `src/ublue_images/files.json`.
- Running `uv run src/ublue_images/tags.py --download` will delete `files/dnf/tags/` and then repopulate it *only* from `src/ublue_images/tags.json`.

When changing recipes that reference `files/dnf/rpms/*` or `files/dnf/tags/*`, keep the corresponding JSON config in sync so that a regeneration doesn’t remove required RPMs.

## Security / signing

- Images are signed and can be verified with cosign:
  - `cosign verify --key cosign.pub ghcr.io/purkkis/kinoite`

## Generated code

- `src/ublue_images/models/github.py` is generated (see `justfile` target `github-release-download`).
- If regenerating, the just target downloads a GitHub API JSON payload and runs `datamodel-codegen` to overwrite that file.
