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

gh release create "$VERSION" \
  .genreleases/learning-content-specifier-template-copilot-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-copilot-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-claude-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-claude-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-gemini-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-gemini-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-cursor-agent-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-cursor-agent-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-opencode-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-opencode-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-qwen-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-qwen-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-windsurf-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-windsurf-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-codex-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-codex-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-kilocode-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-kilocode-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-auggie-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-auggie-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-roo-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-roo-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-codebuddy-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-codebuddy-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-qoder-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-qoder-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-amp-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-amp-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-shai-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-shai-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-q-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-q-ps-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-bob-sh-"$VERSION".zip \
  .genreleases/learning-content-specifier-template-bob-ps-"$VERSION".zip \
  .genreleases/lcs-contracts-"$VERSION".zip \
  --title "LCS Templates - $VERSION_NO_V" \
  --notes-file release_notes.md
