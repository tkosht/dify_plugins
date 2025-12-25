# Agent Skills Research 2025-12-24

Tags: agent-skills, skill-authoring, codex, skill-creator

## Problem
Need a precise picture of Agent Skills in this repository and a reusable skill for creating skills.

## Research
- Skill locations observed:
  - `.codex/skills/.system/` (system skills)
  - `skills/.system/` (repo copy of system skills)
  - `.claude/skills/` (project-local skills)
  - `.codex/skills/` (symlinks for discovery)
- Existing skills and sources:
  - `skill-creator`: `.codex/skills/.system/skill-creator/SKILL.md`
  - `skill-installer`: `.codex/skills/.system/skill-installer/SKILL.md`
  - `codex-subagent`: `.claude/skills/codex-subagent/SKILL.md`
- Skill structure and trigger rule confirmed from `skill-creator` documentation.
- Skills feature enabled in `.codex/config.toml`.
- No `*skill*` tests were found under `tests/`.

## Solution
- Added project-local skill `skill-authoring` under `.claude/skills/skill-authoring/`.
- Added detailed reference: `.claude/skills/skill-authoring/references/agent_skills_overview.md`.
- Added symlink for discovery: `.codex/skills/skill-authoring`.

## Verification
- `rg --files -uu -g 'SKILL.md'`
- `eza -la .codex/skills`
- `sed -n '1,200p' .codex/skills/.system/skill-creator/SKILL.md`
