# Git Flow Policy

## Branches

- `main`: production-ready branch
- `dev`: integration branch
- `feat/*` or `feature/*`: feature development branches from `dev`

## Commit Convention

Use Angular conventional commit messages, such as:

- `feat: add backup stage orchestration`
- `fix: handle empty extension input`
- `docs: update privacy boundary`

## Worktree Policy

Do not use git worktree in this project.

## Tagged Packaging Release

Maintainer-facing packaging workflow is defined in `.github/workflows/package.yml`.

- Trigger: push a tag matching `v*` (for example `v0.0.1`).
- Build output: Windows package artifact `ark-<version>-windows-x64.zip`.
- Release behavior: creates a draft GitHub Release and attaches the zip.

Recommended release sequence:

```bash
python3 -m pytest -q
git tag v0.0.1
git push origin v0.0.1
```
