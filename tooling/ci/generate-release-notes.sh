#!/usr/bin/env bash
set -euo pipefail

# generate-release-notes.sh
# Generate release notes from git history
# Usage: generate-release-notes.sh <new_version> <last_tag>

if [[ $# -ne 1 && $# -ne 2 ]]; then
  echo "Usage: $0 <new_version> [last_tag]" >&2
  exit 1
fi

NEW_VERSION="$1"
LAST_TAG="${2:-}"

if [[ ! "$NEW_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v0.0.0" >&2
  exit 1
fi

VERSION_NO_V="${NEW_VERSION#v}"

extract_changelog_section() {
  local version_no_v="$1"
  [[ -f CHANGELOG.md ]] || return 1

  awk -v v="$version_no_v" '
    BEGIN { in_section=0 }
    $0 ~ "^## \\[[0-9]+\\.[0-9]+\\.[0-9]+\\] - " {
      if (in_section) exit
      if ($0 ~ "^## \\"" "\\[" v "\\] - ") { in_section=1; next }
    }
    in_section { print }
  ' CHANGELOG.md | sed '/^[[:space:]]*$/d'
}

COMMITS=""
CHANGELOG_NOTES=$(extract_changelog_section "$VERSION_NO_V" || true)

if [[ -n "$CHANGELOG_NOTES" ]]; then
  COMMITS="$CHANGELOG_NOTES"
else
  if [[ -z "$LAST_TAG" ]]; then
    LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
  fi

# Get commits since last tag
  if [ "$LAST_TAG" = "v0.0.0" ]; then
    # Check how many commits we have and use that as the limit
    COMMIT_COUNT=$(git rev-list --count HEAD)
    if [ "$COMMIT_COUNT" -gt 10 ]; then
      COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~10..HEAD)
    else
      COMMITS=$(git log --oneline --pretty=format:"- %s" HEAD~$COMMIT_COUNT..HEAD 2>/dev/null || git log --oneline --pretty=format:"- %s")
    fi
  else
    COMMITS=$(git log --oneline --pretty=format:"- %s" $LAST_TAG..HEAD)
  fi
fi

# Create release notes
cat > release_notes.md << EOF
This is the latest set of releases that you can use with your agent of choice. We recommend using the LCS CLI to scaffold your projects, however you can download these independently and manage them yourself.

## Changelog

$COMMITS

EOF

echo "Generated release notes:"
cat release_notes.md
