# Branch Strategy Memory

## Branch Hierarchy
- **main**: Production-ready code, stable releases only
- **integrate**: Integration testing, pre-production staging
- **dev**: Active development base branch
- **feature/[name]**: Individual features, created from dev

## Development Workflow
1. **Start Feature**: `git checkout dev && git pull && git checkout -b feature/[name]`
2. **Develop**: Work on feature branch, commit regularly
3. **Complete**: `git checkout dev && git merge feature/[name] && git branch -d feature/[name]`
4. **Integrate**: `git checkout integrate && git merge dev`
5. **Release**: `git checkout main && git merge integrate && git tag v[version]`

## Branch Rules
- Never commit directly to main or integrate
- Always create feature branches from dev
- Delete feature branches after merge
- Test on integrate before main
- Use conventional commit messages

## Conventional Commits
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `style:` Code style
- `refactor:` Code refactoring
- `test:` Test additions
- `chore:` Maintenance

## Emergency Hotfix
1. `git checkout main && git checkout -b hotfix/[issue]`
2. Fix the issue
3. `git checkout main && git merge hotfix/[issue] && git tag v[patch]`
4. Backport to dev and integrate branches

## Merge Strategy
- Feature branches: Fast-forward merge
- Dev to integrate: Merge commit
- Integrate to main: Merge commit
- Hotfix: Direct merge to main
