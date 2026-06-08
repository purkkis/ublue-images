#! /bin/bash
set -euo pipefail

# Array to hold Fedora versions
FEDORA_VERSIONS=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
    -* | --*)
        echo "Unknown option $1"
        exit 1
        ;;
    *)
        # Treat as Fedora version
        FEDORA_VERSIONS+=("$1")
        shift
        ;;
    esac
done

# If no versions were specified, show usage and exit
if [ ${#FEDORA_VERSIONS[@]} -eq 0 ]; then
    echo "Usage: $0 <fedora_version> [fedora_version ...]"
    echo "Example: $0 43 44"
    exit 1
fi

command -v just >/dev/null 2>&1 || {
    echo >&2 "just is required but not installed. Aborting."
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"/files/dropbox

# Build for each specified version
for version in "${FEDORA_VERSIONS[@]}"; do
    just build "$version"
done
