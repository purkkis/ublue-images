# AGENTS.md

## What this repo is

This repository builds custom Fedora Atomic desktop images using **BlueBuild** recipes.

- BlueBuild recipes live in `recipes/`.
- Custom artifacts (DNF repo files, vendored RPMs, copied system files) live in `files/`.
- GitHub Actions builds/publishes images via `blue-build/github-action@v1`.

## Quick commands

### Build images locally

Requires `bluebuild` and `just`.

- `just build-kinoite`
- `just build-kinoite-nvidia`

### Generate ISOs

- `just kinoite-iso`
- `just kinoite-nvidia-iso`

### Download RPMs

- `uv run scripts/download_rpms.py download` - Download all RPMs from `scripts/rpms.json`
- `uv run scripts/download_rpms.py cache-info` - Generate cache info for CI

### Build Dropbox RPMs

- `./build-dropbox.sh <fedora_version> [fedora_version ...]` - e.g., `./build-dropbox.sh 42 43`

### Formatting

- `prek run --all-files` - Run all pre-commit hooks (trailing whitespace, EOF, YAML/JSON validity, LF endings, ruff)

## Python environment

Uses **uv** for dependency management. Python >=3.11.

- Run scripts with `uv run <command>` - it handles virtual environments automatically

## Repository layout

- `recipes/`: BlueBuild recipes (`kinoite.yml`, `kinoite-nvidia.yml`) and shared fragments (`_*.yml`)
- `scripts/`: Python scripts (`download_rpms.py`) and config (`rpms.json`)
- `files/dnf/`: DNF `.repo` files and vendored RPMs
- `files/dropbox/`: Docker-based Dropbox RPM builder
- `.github/workflows/`: CI pipelines

## BlueBuild recipe patterns

### Schemas

All YAMLs include schema headers:

- Recipes: `# yaml-language-server: $schema=https://schema.blue-build.org/recipe-v1.json`
- Module fragments: `# yaml-language-server: $schema=https://schema.blue-build.org/module-list-v1.json`

### Composition

Recipes compose shared fragments via `from-file`:

- `_common-brew.yml` - Homebrew setup
- `_kinoite-dnf.yml` - DNF repos and packages
- `_common-flatpaks.yml` - System Flatpaks
- `_kinoite-fonts.yaml` - Font packages
- `_kinoite-docker.yml` - Docker CE
- `_boot_to_windows.yml` - Boot-to-Windows utility
- `_chatwise-desktop-fix.yml` - Desktop file fix script

NVIDIA variant adds `akmods` module with `nvidia-open` driver.

### YAML conventions

- Keep list items in **alphabetical order**
- For URLs, sort by filename not the URL itself

## RPM management

RPMs are managed via `scripts/rpms.json` and `scripts/download_rpms.py`.

### Two types of RPMs

1. **Pinned**: Fixed URLs with explicit cache keys
   - Format: `{"url": "...", "filename": "...", "cache_key": "..."}`
   - Example: Positron, ProtonMail Bridge

2. **Latest**: Auto-fetch from GitHub releases
   - Format: `{"github_owner": "...", "github_repo": "...", "filename": "..."}`
   - Example: Chatwise, DBeaver
   - Queries GitHub API for latest x86_64 RPM asset

### Adding a new RPM

1. Add entry to `scripts/rpms.json` (pinned or latest format)
2. Run `uv run scripts/download_rpms.py download`
3. Reference by filename in a DNF module (e.g., `recipes/_kinoite-dnf.yml`)

### Dropbox RPMs

- Built using Docker container that compiles from source with patches
- Version tag in `files/dropbox/justfile` as `docker_tag`
- Must match filenames in `recipes/_kinoite-dnf.yml`

## CI caching

- RPM cache key includes all versions (pinned cache keys + GitHub release tags)
- To invalidate pinned RPM cache: update both URL and `cache_key` in `rpms.json`
- Latest RPMs auto-invalidate when new GitHub release detected

## Important gotchas

- **Fedora version updates**: Update `image-version` in both recipes, Dropbox RPM reference in `_kinoite-dnf.yml`, and build new Dropbox RPM
- **RPM download skips existing files**: Script won't re-download if file exists with non-zero size
- **ISO scripts only cover Kinoite variants**: No other desktop environments in `justfile`
