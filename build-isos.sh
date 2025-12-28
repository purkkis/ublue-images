#! /bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check dependencies
BLUEBUILD_BIN=$(command -v bluebuild) || {
    echo >&2 "bluebuild is required but not installed. Aborting."
    exit 1
}
command -v aws >/dev/null 2>&1 || {
    echo >&2 "aws cli is required but not installed. Aborting."
    exit 1
}

# Check environment variables
if [[ -z "${B2_ENDPOINT:-}" ]]; then
    echo "Error: B2_ENDPOINT is not set"
    exit 1
fi
if [[ -z "${B2_BUCKET_NAME:-}" ]]; then
    echo "Error: B2_BUCKET_NAME is not set"
    exit 1
fi
if [[ -z "${AWS_ACCESS_KEY_ID:-}" ]]; then
    echo "Error: AWS_ACCESS_KEY_ID is not set"
    exit 1
fi
if [[ -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
    echo "Error: AWS_SECRET_ACCESS_KEY is not set"
    exit 1
fi

upload_iso() {
    local iso_name="$1"
    aws --endpoint-url="https://$B2_ENDPOINT" s3 cp --no-progress "$iso_name" "s3://$B2_BUCKET_NAME/bluebuild/$iso_name"
    aws --endpoint-url="https://$B2_ENDPOINT" s3 cp --no-progress "$iso_name-CHECKSUM" "s3://$B2_BUCKET_NAME/bluebuild/$iso_name-CHECKSUM"
}

build_and_upload() {
    local iso_name="$1"
    local image="$2"
    "$BLUEBUILD_BIN" generate-iso --iso-name "$iso_name" image "$image"
    upload_iso "$iso_name"
    rm "$iso_name" "$iso_name-CHECKSUM"
}

# build_and_upload "kinoite.iso" "ghcr.io/purkkis/kinoite:daily"
build_and_upload "kinoite-nvidia.iso" "ghcr.io/purkkis/kinoite-nvidia:daily"
