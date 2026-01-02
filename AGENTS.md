# ublue-images (Developer Notes)

## Repository Layout

```
recipes/                      BlueBuild recipes + shared modules (prefixed with `_`)
  kinoite.yml                 Base image recipe (image-version: 43)
  kinoite-nvidia.yml          NVIDIA variant recipe (image-version: 43)
  _kinoite-dnf.yml            DNF repos + packages + local/tagged RPM installs
  _common-flatpaks.yml        Flatpaks installed system-wide
  _common-brew.yml            Homebrew module configuration (nofile-limits, no auto-upgrade)
  _sysusers.yml               systemd-sysusers setup (copies sysusers.d files)
  _scripts.yml                Post-install tweaks (desktop file edits)
  _amd-rocm.yml               RPMFusion + AMD/ROCm packages (used by kinoite.yml)
  _kinoite-docker.yml         Docker repo + docker packages + enable docker.service
  _kinoite-fonts.yaml         Nerd Fonts + Google fonts

files/
  dnf/                        DNF repo files and RPMs used by recipes
    *.repo                    Repo configuration consumed by recipes/_kinoite-dnf.yml
    dropbox-f43.rpm           Locally built RPM (see files/dropbox/)
    rpms/                     "Hardcoded/managed" RPMs (see src/ublue_images/files.json)
    tags/                     "Latest GitHub release tag" RPMs (see src/ublue_images/tags.json)
  usr_lib_sysusers_d/         sysusers.d entries copied into /usr/lib/sysusers.d
  dropbox/                    Docker-based build context + justfile to produce dropbox RPMs

src/ublue_images/
  github_release_download.py  GitHub release/tag lookup + download helpers
  rpms.py                     Download RPMs from src/ublue_images/files.json -> files/dnf/rpms/
  tags.py                     Refresh tags.json and download tagged RPMs -> files/dnf/tags/
  models/github.py            Pydantic model generated via datamodel-codegen

.github/workflows/
  build.yml                   Nightly image builds + auto-update tags.json
  build-iso.yml               Weekly ISO builds + upload to B2 (runs build-isos.sh)
```

## Developer Commands

```bash
# RPM management
just update-github-release-tags  # Refresh tags.json from GitHub
uv run src/ublue_images/tags.py --download  # Download tagged RPMs
uv run src/ublue_images/rpms.py  # Download hardcoded RPMs

# Build dropbox RPMs
./build-dropbox.sh 42 43

# ISO builds (requires env vars: B2_ENDPOINT, B2_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
./build-isos.sh <iso_name> <image>
```

## CI Workflows

### build.yml

- `update-tags`: Refreshes GitHub release tags in tags.json and auto-commits
- `bluebuild`: Builds kinoite and kinoite-nvidia images on ubicloud-standard-4
- `delete-package-versions`: Removes images older than 1 day from registry

### build-iso.yml

- Weekly ISO builds on ubicloud-standard-4
- Installs bluebuild and calls build-isos.sh

## Code Conventions

### Python

- Python >=3.11,<4.0
- Ruff: line-length 100, indent-width 4

### Pre-commit

- whitespace/yaml/json/toml hygiene
- mixed-line-ending with --fix=lf
- ruff-check (imports: --select I --fix)
- ruff-format
- gitleaks

## BlueBuild Recipe Patterns

- Recipes reference shared modules via `from-file: _something.yml`
- Module lists include `$schema` header (recipe-v1.json or module-list-v1.json)
- Lists are kept in alphabetical order
- Module order matters (dependencies first, `type: signing` last)

### Key Modules

- `_sysusers.yml`: Copies `files/usr_lib_sysusers_d/*` to `/usr/lib/sysusers.d` and runs systemd-sysusers
- `_scripts.yml`: Patches .desktop Exec lines with sed
- `_kinoite-dnf.yml`: Installs from .repo files, local RPMs, and downloaded RPMs
- `kinoite-nvidia.yml`: Includes akmods with nvidia-open, adds Steam from negativo17

## Vendored RPM Workflow

Two automation paths:

1. **Hardcoded**: `src/ublue_images/files.json` -> `files/dnf/rpms/`
2. **Latest-tag**: `src/ublue_images/tags.json` -> `files/dnf/tags/`

### JSON Structure

Both use Pydantic model `ReleaseItems` with: name, tag, url, enabled, repo (optional)

### Gotcha: Download Scripts Delete Directories

`GitHubReleaseDownloader.download_files()` removes and recreates the output directory.

Running:
- `uv run src/ublue_images/rpms.py` deletes and repopulates `files/dnf/rpms/` from files.json
- `uv run src/ublue_images/tags.py --download` deletes and repopulates `files/dnf/tags/` from tags.json

When changing recipes that reference these paths, keep the JSON config in sync.

## Generated Code

- `src/ublue_images/models/github.py` is generated via `just github-release-download`
