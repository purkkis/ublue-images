# Custom Fedora Atomic Images (ublue-images)

[![bluebuild build badge](https://github.com/purkkis/ublue-images/actions/workflows/build.yml/badge.svg)](https://github.com/purkkis/ublue-images/actions/workflows/build.yml)

This repository builds custom Fedora Atomic desktop images using [BlueBuild](https://blue-build.org/) recipes.

## Available Images

### Kinoite (KDE Plasma)

- **Base**: `ghcr.io/ublue-os/kinoite-main`
- **Image**: `ghcr.io/purkkis/kinoite`
- **NVIDIA Variant**: `ghcr.io/purkkis/kinoite-nvidia`

### Aurora (KDE Plasma - Aurora DX Fork)

_Note: Aurora images can be built locally but are currently disabled in CI._

- **Image**: `ghcr.io/purkkis/aurora`
- **NVIDIA Variant**: `ghcr.io/purkkis/aurora-nvidia`

## Installation

The recommended way to install these images is to generate an ISO and perform a fresh installation.

1. **Generate the ISO** (see [Local Build](#local-build--development) below):

   ```bash
   just kinoite-iso
   # or
   just kinoite-nvidia-iso
   ```

2. **Flash the ISO** to a USB drive (using e.g. [Fedora Media Writer](https://docs.fedoraproject.org/en-US/fedora/latest/preparing-boot-media/#_fedora_media_writer)).

3. **Install** the OS, selecting your computed ISO as the source.

## Local Build & Development

This repository uses `just` for convenient local commands.

### Build Images

```bash
# Build Kinoite
just build-kinoite

# Build Kinoite (NVIDIA)
just build-kinoite-nvidia

# Build Aurora
just build-aurora
```

### Generate ISOs

Requires `bluebuild` installed locally.

```bash
just kinoite-iso
just kinoite-nvidia-iso
```

## Verification

Images are signed with Sigstore's cosign.

```bash
cosign verify --key cosign.pub ghcr.io/purkkis/kinoite
```
