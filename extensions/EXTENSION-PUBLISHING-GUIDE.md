# Extension Publishing Guide

## Intent

Publish extensions that are installable, verifiable, and schema-compatible with current LCS runtime.

## Pre-Publish Requirements

- Manifest passes validation with `requires.lcs_version`.
- Hook events use clean-break names.
- Commands follow `lcs.<extension-id>.<command>` naming.
- README includes install/usage/configuration instructions.
- CHANGELOG documents breaking changes.

## Package Layout

Required files:

- `extension.yml`
- `commands/*.md`
- `README.md`

Optional:

- config templates
- examples
- migration notes

## Versioning

- Use semantic versioning for extension release.
- Bump MAJOR for breaking manifest/command changes.
- Bump MINOR for backward-compatible features.
- Bump PATCH for fixes/docs.

## Publish Steps

1. Validate locally (`lcs extension add --dev ...`).
2. Tag release in your extension repo.
3. Publish artifact (zip) and metadata.
4. Update catalog entry (if catalog-based distribution is used).

## Catalog Entry Checklist

- `id`, `name`, `version`, `description`
- `download_url` (HTTPS)
- `author`, `tags`
- compatibility notes for `lcs_version`

## Failure Modes

- Invalid manifest key (`speckit_version`) blocks install.
- Legacy hook names block install.
- Non-HTTPS download URL is rejected.

## Migration Guidance for Consumers

If upgrading from legacy extension versions:

- map legacy sequence hook name -> `after_sequence`
- map legacy author hook name -> `after_author`
- map `SPECKIT_*` env vars -> `LCS_*`
