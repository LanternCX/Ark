# Superpowers Overrides For Ark

This repository defines project-level overrides on top of the installed superpowers defaults.

## Overrides

1. Do not use git worktree. Use direct branch switching only.
2. Keep all production code and comments in English.
3. Maintain bilingual documentation (`README.md` and `README.zh-CN.md`).
4. Enforce Git Flow branch model (`main`, `dev`, `feat/*`, `feature/*`).
5. Use `questionary + rich` for TUI components.
6. Use `litellm` as the LLM routing layer.
7. Apply project-local skills under `.opencode/skills/`:
   - `.opencode/skills/code-standard/SKILL.md`
   - `.opencode/skills/doc-maintainer/SKILL.md`
   - `.opencode/skills/git-workflow/SKILL.md`
