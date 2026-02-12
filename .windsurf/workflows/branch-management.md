---
description: Quản lý branches cho local development workflow
---

# Branch Management Workflow

## Branch Structure

- **main**: Production-ready code, stable releases
- **integrate**: Integration testing, pre-production
- **dev**: Active development base
- **feature/[name]**: Individual features from dev

## Workflow Commands

### 1. Start New Feature
```bash
git checkout dev
git pull origin dev
git checkout -b feature/[feature-name]
```

### 2. Feature Development
- Work on feature branch
- Commit regularly with conventional commits
- Push to remote for backup

### 3. Feature Complete
```bash
git checkout dev
git pull origin dev
git merge feature/[feature-name]
git push origin dev
git branch -d feature/[feature-name]
```

### 4. Integration Testing
```bash
git checkout integrate
git pull origin integrate
git merge dev
git push origin integrate
```

### 5. Production Release
```bash
git checkout main
git pull origin main
git merge integrate
git tag v[version]
git push origin main
git push origin v[version]
```

## Branch Rules

- **Never commit directly to main**
- **Always create feature branches from dev**
- **Test on integrate before main**
- **Use conventional commit messages**
- **Delete feature branches after merge**

## Conventional Commits

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style
- `refactor:` Code refactoring
- `test:` Test additions
- `chore:` Maintenance

## Emergency Hotfix

```bash
git checkout main
git pull origin main
git checkout -b hotfix/[issue]
# Fix the issue
git checkout main
git merge hotfix/[issue]
git tag v[patch-version]
git push origin main
git push origin v[patch-version]
```
