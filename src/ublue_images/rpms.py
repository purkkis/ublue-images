from loguru import logger

from ublue_images.github_release_download import rpms

if __name__ == "__main__":
    try:
        rpms()
    except Exception:
        logger.exception("Failed to download RPMs")
        exit(1)
