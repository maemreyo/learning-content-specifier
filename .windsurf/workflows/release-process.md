---
description: Quy trình release sản phẩm từ development đến production
---

# Release Process Workflow

## Pre-Release Checklist

### 1. Code Quality
- [ ] All tests passing
- [ ] Code review completed
- [ ] Linting checks passed
- [ ] Documentation updated

### 2. Integration Testing
- [ ] Features tested on `integrate` branch
- [ ] No merge conflicts
- [ ] Performance tests passed
- [ ] Security checks completed

### 3. Version Planning
- [ ] Version number determined (semantic versioning)
- [ ] Release notes prepared
- [ ] Breaking changes documented
- [ ] Migration guides updated

## Release Types

### 🔄 Patch Release (x.x.X)
```bash
# For bug fixes only
git checkout main
git pull origin main
git tag v1.0.1
git push origin main
git push origin v1.0.1
```

### ⚡ Minor Release (x.X.x)
```bash
# For new features (backward compatible)
git checkout main
git pull origin main
git merge integrate
git tag v1.1.0
git push origin main
git push origin v1.1.0
```

### 🚀 Major Release (X.x.x)
```bash
# For breaking changes
git checkout main
git pull origin main
git merge integrate
git tag v2.0.0
git push origin main
git push origin v2.0.0
```

## Step-by-Step Release

### 1. Prepare Release Branch
```bash
git checkout dev
git pull origin dev
git checkout -b release/v[version]
```

### 2. Final Testing
```bash
# Run full test suite
python3 -m pytest tests/
# Check code quality
python3 -m flake8 src/
# Run integration tests
python3 -m pytest tests/integration/
```

### 3. Update Version Files
```bash
# Update pyproject.toml version
# Update CHANGELOG.md
# Update README.md if needed
```

### 4. Merge to Integration
```bash
git checkout integrate
git pull origin integrate
git merge release/v[version]
git push origin integrate
```

### 5. Final Integration Test
```bash
# Run production-like tests
# Verify deployment configuration
# Check documentation
```

### 6. Release to Production
```bash
git checkout main
git pull origin main
git merge integrate
git tag v[version]
git push origin main
git push origin v[version]
```

### 7. Post-Release
```bash
# Clean up release branch
git branch -d release/v[version]
# Update development branch
git checkout dev
git merge main
git push origin dev
```

## Version Numbering

### Semantic Versioning (SemVer)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Examples
- `v1.0.0` - First stable release
- `v1.1.0` - Added new features
- `v1.1.1` - Bug fix
- `v2.0.0` - Breaking changes

## Release Notes Template

```markdown
# Release v[version]

## 🚀 Features
- Feature 1 description
- Feature 2 description

## 🐛 Fixes
- Bug fix 1 description
- Bug fix 2 description

## 💥 Breaking Changes
- Breaking change 1 description
- Breaking change 2 description

## 📝 Documentation
- Updated documentation for X
- Added guide for Y

## 🔧 Dependencies
- Updated dependency X to version Y
```

## Emergency Hotfix

### 1. Create Hotfix Branch
```bash
git checkout main
git pull origin main
git checkout -b hotfix/[issue-number]
```

### 2. Fix and Test
```bash
# Make the fix
# Test thoroughly
# Update version as patch
```

### 3. Release Hotfix
```bash
git checkout main
git merge hotfix/[issue-number]
git tag v[patch-version]
git push origin main
git push origin v[patch-version]
```

### 4. Backport to Other Branches
```bash
git checkout integrate
git merge main
git push origin integrate

git checkout dev
git merge main
git push origin dev
```

## Rollback Procedure

### 1. Identify Problem
```bash
git log --oneline -10
git tag --list
```

### 2. Rollback to Previous Version
```bash
git checkout main
git pull origin main
git revert [commit-hash]
git tag v[rollback-version]
git push origin main
git push origin v[rollback-version]
```

### 3. Communicate
- Notify team about rollback
- Document root cause
- Plan next steps
