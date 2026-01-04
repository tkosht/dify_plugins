# Agent Skills Overview (Repository)

## Current Skill Locations
- `.codex/skills/.system/` contains system skills (`skill-creator`, `skill-installer`) and `.codex-system-skills.marker`.
- `.claude/skills/` stores project-local skills (currently `codex-subagent`).
- `.codex/skills/` holds symlinks to project-local skills for discovery (currently `codex-subagent`).
- `.codex/config.toml` enables skills via `[features] skills = true`.
- No repo-level `skills/` directory is expected; keep system skills under `.codex/skills/.system`.

## Existing Skills
- `skill-creator`: Defines skill anatomy, naming, frontmatter rules, optional resources, and packaging scripts.
  - File: `.codex/skills/.system/skill-creator/SKILL.md`
- `skill-installer`: Installs skills from curated lists or GitHub repos.
  - File: `.codex/skills/.system/skill-installer/SKILL.md`
- `codex-subagent`: Project-local skill to orchestrate `codex exec` runs (single/parallel/competition) with logging and guardrails.
  - Files: `.claude/skills/codex-subagent/SKILL.md`, `.claude/skills/codex-subagent/scripts/*`, `.codex/skills/codex-subagent`

## Templates (Non-skill References)
- Subagent SKILL.md template: `.claude/skills/skill-authoring/references/subagent_skill_md_template.md`

## Skill Structure (From skill-creator)
- Required: `SKILL.md` with YAML frontmatter containing `name` and `description`.
- `description` is the primary trigger text for when the skill is selected.
- Optional resource folders:
  - `scripts/` for deterministic helpers
  - `references/` for detailed docs
  - `assets/` for templates or files used in output

## Helper Scripts (System Skill)
Located under `.codex/skills/.system/skill-creator/scripts/`:
- `init_skill.py` (scaffold a new skill)
- `quick_validate.py` (validate structure)
- `package_skill.py` (package to .skill)

Local policy: do not add a top-level `scripts/` directory. If you run any of the helper scripts, invoke Python with `uv run python` or `python3`.

## Tests
No skill-related test files were found under `tests/` using `rg --files -g '*skill*' tests`.
