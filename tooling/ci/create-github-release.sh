#!/usr/bin/env bash
set -euo pipefail

# create-github-release.sh
# Create a GitHub release with all template zip files
# Usage: create-github-release.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

# Remove 'v' prefix from version for release title
VERSION_NO_V=${VERSION#v}

if [[ ! -d .genreleases ]]; then
  echo "Missing .genreleases directory" >&2
  exit 1
fi

mapfile -t ASSETS < <(find .genreleases -maxdepth 1 -type f | sort)
if [[ ${#ASSETS[@]} -eq 0 ]]; then
  echo "No release assets found in .genreleases" >&2
  exit 1
fi

gh release create "$VERSION" \
  "${ASSETS[@]}" \
  --title "LCS Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
