# Custom Fedora Atomic Images (ublue-images)

[![bluebuild build badge](https://github.com/purkkis/ublue-images/actions/workflows/build.yml/badge.svg)](https://github.com/purkkis/ublue-images/actions/workflows/build.yml)

This repository builds custom Fedora Atomic desktop images using [BlueBuild](https://blue-build.org/) recipes.

## Available Images

### Kinoite (KDE Plasma)

- **Base**: `ghcr.io/ublue-os/kinoite-main`
- **Image**: `ghcr.io/purkkis/kinoite`
- **NVIDIA Variant**: `ghcr.io/purkkis/kinoite-nvidia`

## Installation

The recommended way to install these images is to generate an ISO and perform a fresh installation.

1. **Generate the ISO** (see [Local Build](#local-build--development) below):

   ```bash
   just build-iso-kinoite-from-ghcr-image
   # or
   just build-iso-kinoite-nvidia-from-ghcr-image
   ```

2. **Flash the ISO** to a USB drive (using e.g. [Fedora Media Writer](https://docs.fedoraproject.org/en-US/fedora/latest/preparing-boot-media/#_fedora_media_writer)).

3. **Install** the OS, selecting your computed ISO as the source.

## Local Build & Development

This repository uses `just` for convenient local commands.

### Build Images

```bash
# Build Kinoite
just build-image-kinoite

# Build Kinoite (NVIDIA)
just build-image-kinoite-nvidia
```

### Generate ISOs

Requires `bluebuild` installed locally.

```bash
just build-iso-kinoite-from-ghcr-image
just build-iso-kinoite-nvidia-from-ghcr-image
```

## Verification

Images are signed with Sigstore's cosign.

```bash
cosign verify --key cosign.pub ghcr.io/purkkis/kinoite
```

## 1Password Groups

The `1password` and `1password-cli` packages contain files that need to be owned by certain groups:

- `/usr/lib/opt/1Password/1Password-BrowserSupport` (owned by `onepassword` group)
- `/usr/bin/op` (owned by `onepassword-cli` group)

The GIDs for these groups are pinned in `sysusers.d` config files. It's likely that we are required to modify the above groups' (that are automatically created by the 1Password RPMs) GIDs to match the pinned GIDs on live host system. This needs to be done only once after the initial installation.

```bash
sudo groupmod -g 1500 onepassword
sudo groupmod -g 1600 onepassword-cli
```
