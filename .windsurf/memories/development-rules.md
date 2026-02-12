# Development Rules Memory

## Code Quality Standards
- All tests must pass before merge
- Code review required for all changes
- Linting checks must pass (flake8, black)
- Documentation updates required for API changes
- Type hints required for new code

## Testing Requirements
- **Unit tests**: Required for all new features
- **Integration tests**: Required for complex changes
- **Manual testing**: Required on integrate branch
- **Performance tests**: Required for major changes
- **Security tests**: Required for authentication/API changes

## Python Specific Rules
- Use `python3` instead of `python`
- Follow PEP 8 style guidelines
- Use type hints (mypy compatible)
- Include docstrings for all public functions
- Maximum line length: 88 characters (black default)

## File Organization
- Source code: `src/` directory
- Tests: `tests/` directory
- Documentation: `docs/` directory
- Templates: `templates/` directory
- Scripts: `scripts/` directory

## Security & Compliance
- No hardcoded secrets or credentials
- Use environment variables for configuration
- Regular dependency security updates
- Security scans before releases
- Follow OWASP guidelines for web components

## Performance Guidelines
- Profile code for performance bottlenecks
- Use appropriate data structures
- Optimize database queries
- Cache when appropriate
- Monitor memory usage

## Documentation Requirements
- README.md for all new features
- API documentation for public interfaces
- Code comments for complex logic
- CHANGELOG.md updates for releases
- Migration guides for breaking changes

## Code Review Process
- At least one reviewer required
- Review focuses on: functionality, security, performance, maintainability
- Automated checks must pass (tests, linting, security)
- Breaking changes need extra review
- Documentation changes reviewed by technical writers

## Dependencies Management
- Use `pyproject.toml` for dependency management
- Pin versions for production stability
- Regular security vulnerability checks
- Test dependency updates before merging
- Minimize dependency footprint

## Error Handling
- Use appropriate exception types
- Provide meaningful error messages
- Log errors appropriately
- Handle edge cases gracefully
- Fail fast for invalid inputs

## Communication Standards
- Use descriptive commit messages
- Update CHANGELOG.md for releases
- Document breaking changes clearly
- Notify team of major changes
- Use issues/PRs for discussions
