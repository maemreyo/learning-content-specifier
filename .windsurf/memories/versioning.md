# Versioning Strategy Memory

## Semantic Versioning (SemVer)
Format: MAJOR.MINOR.PATCH
- **MAJOR** (X.x.x): Breaking changes, incompatible API changes
- **MINOR** (x.X.x): New features, backward compatible additions
- **PATCH** (x.x.X): Bug fixes, backward compatible fixes

## Current State
- **Base**: Forked from original repo with clean history
- **Current Tag**: fork-start (forking point)
- **Next Version**: v1.0.0 (first stable release)

## Release Types
### Patch Release (v1.0.1, v1.0.2)
- Critical bug fixes
- Security vulnerabilities
- Documentation fixes
- Performance improvements

### Minor Release (v1.1.0, v1.2.0)
- New features (backward compatible)
- Enhanced functionality
- API additions
- Major documentation updates

### Major Release (v2.0.0, v3.0.0)
- Breaking changes
- API redesign
- Major architecture changes
- Deprecation of old features

## Version Files to Update
- `pyproject.toml` - version field
- `CHANGELOG.md` - release notes
- `README.md` - version badge (if applicable)
- `src/lcs_cli/__init__.py` - version constant

## Tag Management
- Always tag main branch releases
- Use semantic version numbers only
- Include release notes with each tag
- Push tags to remote repository

## Pre-Release Versions (Optional)
- Alpha: v1.0.0-alpha.1 (early development)
- Beta: v1.0.0-beta.1 (feature complete, testing)
- RC: v1.0.0-rc.1 (release candidate, production ready)

## Branch Version Mapping
- **main**: Latest stable version (e.g., v1.0.0)
- **integrate**: Next release candidate (e.g., v1.1.0-rc.1)
- **dev**: Next development version (e.g., v1.1.0-alpha.1)
- **feature branches**: Feature-specific versions

## Release Process
1. Prepare release branch from dev
2. Update version files
3. Run full test suite
4. Merge to integrate for final testing
5. Merge to main and create tag
6. Push tag and update changelog
