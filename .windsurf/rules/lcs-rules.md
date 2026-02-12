# LCS (Learning Content Specifier) Development Rules

## Project Overview
LCS is a comprehensive toolkit for implementing Spec-Driven Development (SDD) - a methodology that emphasizes creating clear specifications before implementation.

## Branch Strategy
- **main**: Production-ready code, stable releases only
- **integrate**: Integration testing, pre-production staging
- **dev**: Active development base branch
- **feature/[name]**: Individual features, created from dev

## Development Workflow
1. Always create feature branches from dev branch
2. Never commit directly to main or integrate
3. Test features on integrate before merging to main
4. Use conventional commit messages (feat:, fix:, docs:, etc.)
5. Delete feature branches after successful merge

## Code Quality Standards
- All tests must pass before merge
- Code review required for all changes
- Linting checks must pass
- Documentation updates required for API changes

## Testing Requirements
- Unit tests for new features
- Integration tests for complex changes
- Manual testing on integrate branch
- Performance tests for major changes

## Python Specific Rules
- Use python3 instead of python
- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Include docstrings for all functions

## File Organization
- Source code in src/ directory
- Tests in tests/ directory
- Documentation in docs/ directory
- Templates in templates/ directory

## Security & Compliance
- No hardcoded secrets or credentials
- Follow security best practices
- Regular dependency updates
- Security scans before releases

## Versioning Strategy
- Follow Semantic Versioning (SemVer): MAJOR.MINOR.PATCH
- MAJOR: Breaking changes, incompatible API changes
- MINOR: New features, backward compatible additions
- PATCH: Bug fixes, backward compatible fixes
- Tag all releases on main branch

## Release Process
1. Prepare release branch from dev
2. Run full test suite and code quality checks
3. Update version files (pyproject.toml, CHANGELOG.md)
4. Merge to integrate branch for final testing
5. Merge to main and create version tag
6. Push tag to remote

## Communication
- Use descriptive commit messages
- Update CHANGELOG.md for releases
- Document breaking changes clearly
- Notify team of major changes

## Conventional Commits
- feat: New feature
- fix: Bug fix
- docs: Documentation only changes
- style: Code style changes (formatting, etc.)
- refactor: Code refactoring
- test: Adding or updating tests
- chore: Maintenance tasks

## Emergency Hotfix
1. Create hotfix branch from main
2. Fix the issue and test thoroughly
3. Merge directly to main
4. Create patch version tag
5. Backport fix to dev and integrate branches

## Code Review Requirements
- At least one reviewer for all changes
- Review focuses on functionality, security, performance
- Automated checks must pass
- Breaking changes need extra review
- Documentation changes reviewed by technical writers

## Dependencies
- Use pyproject.toml for dependency management
- Pin versions for production stability
- Regular security updates required
- Test dependency updates before merging
