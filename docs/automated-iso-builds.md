# Automated ISO Builds

This document outlines how to configure your system to run automated ISO builds using `bluebuild generate-iso` without requiring interactive password entry.

## The Problem

The `bluebuild generate-iso` command uses a container to build the ISO. This container requires access to loop devices (via `losetup`) to create the filesystem image. Standard Docker containers are unprivileged and cannot access loop devices, causing the build to fail with:

```
losetup: ... failed to set up loop device: No such file or directory
```

To fix this, the build command must be run with privileges. The `build-isos.sh` script has been updated to use `sudo` for this purpose. However, for automated scripts (like cron jobs or background tasks), interactive password prompts are not feasible.

## The Solution: Passwordless Sudo

You can configure `sudo` to allow a specific user to run the `bluebuild` command as root without being prompted for a password.

### 1. Identify the BlueBuild Binary Path

First, find the absolute path to your `bluebuild` binary:

```bash
which bluebuild
```

Assuming it is located at `/home/<user>/.cargo/bin/bluebuild`.

### 2. Create a Sudoers Configuration

Create a new file in `/etc/sudoers.d/` to grant the permission. Do not edit `/etc/sudoers` directly.

**File:** `/etc/sudoers.d/bluebuild-iso`

**Content:**

```
<user> ALL=(root) NOPASSWD: /home/<user>/.cargo/bin/bluebuild
```

_Replace `<user>` with your actual username and the path with the one found in step 1._

To create this file, run:

```bash
echo "<user> ALL=(root) NOPASSWD: /home/<user>/.cargo/bin/bluebuild" | sudo tee /etc/sudoers.d/bluebuild-iso
sudo chmod 440 /etc/sudoers.d/bluebuild-iso
```

Once this configuration is in place, the `build-isos.sh` script (which already uses `sudo`) will run without prompting for a password.

## Alternative: Podman

If you prefer not to use `sudo`, you can try using Podman instead of Docker. Podman is designed to run rootless containers. However, accessing loop devices from a rootless container can still be complex and may require specific system configurations or running Podman in a privileged mode. The `sudo` method with Docker is generally the most reliable for this specific use case.
