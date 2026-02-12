#!/usr/bin/env bash
set -euo pipefail

# validate-release-version.sh
# Strict release validation for tag-driven releases.
# Usage: validate-release-version.sh <version>

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  exit 1
fi

VERSION="$1"

if [[ ! "$VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Error: version must look like v0.0.0 (got: $VERSION)" >&2
  exit 1
fi

# Ensure we have the latest tags and main reference.
# On workflow_dispatch, checkout is usually main and tags may not be present.
git fetch --tags origin >/dev/null 2>&1 || true
git fetch origin main >/dev/null 2>&1 || true

# Verify tag exists locally after fetch.
if ! git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
  echo "Error: tag not found: $VERSION" >&2
  exit 1
fi

TAG_SHA=$(git rev-list -n 1 "$VERSION")
MAIN_SHA=$(git rev-parse "origin/main")

# Enforce: tag commit must be reachable from main.
if ! git merge-base --is-ancestor "$TAG_SHA" "$MAIN_SHA"; then
  echo "Error: tag $VERSION ($TAG_SHA) is not on origin/main ($MAIN_SHA)" >&2
  exit 1
fi

PYPROJECT_VERSION=""
if [[ -f pyproject.toml ]]; then
  PYPROJECT_VERSION=$(awk -F'"' '/^version[[:space:]]*=[[:space:]]*"/ {print $2; exit}' pyproject.toml || true)
fi

EXPECTED_PY_VERSION="${VERSION#v}"

if [[ -z "$PYPROJECT_VERSION" ]]; then
  echo "Error: could not read version from pyproject.toml" >&2
  exit 1
fi

if [[ "$PYPROJECT_VERSION" != "$EXPECTED_PY_VERSION" ]]; then
  echo "Error: pyproject.toml version ($PYPROJECT_VERSION) does not match tag ($EXPECTED_PY_VERSION)" >&2
  exit 1
fi

if [[ ! -f CHANGELOG.md ]]; then
  echo "Error: CHANGELOG.md not found" >&2
  exit 1
fi

# Require changelog section: ## [X.Y.Z] - YYYY-MM-DD
if ! grep -Eq "^## \[${EXPECTED_PY_VERSION//./\\.}\] - [0-9]{4}-[0-9]{2}-[0-9]{2}$" CHANGELOG.md; then
  echo "Error: CHANGELOG.md missing section header for ${EXPECTED_PY_VERSION} (expected: ## [${EXPECTED_PY_VERSION}] - YYYY-MM-DD)" >&2
  exit 1
fi

echo "Strict release validation passed for $VERSION"
