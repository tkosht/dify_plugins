# Root Directories Investigation 2025-12-31

Tags: repo-structure, codex, skills, sessions, directories

## Problem
Identify why top-level directories `skills/`, `memories/`, `cache/`, `tools/`, and `sessions/` exist in the repo root.

## Research
- `skills/` was tracked and contained `.system` with system skills and a marker file; commit `67676f6` added these files.
- `memory-bank/03-patterns/agent_skills_overview_2025-12-24.md` documented `skills/.system/` as a repo copy of system skills.
- `.claude/skills/skill-authoring/references/agent_skills_overview.md` now states no repo-level `skills/` directory and keeps system skills under `.codex/skills/.system`.
- `pyproject.toml` now references `.codex/skills/.system/skill-creator/scripts/*.py` for lint configuration.
- `sessions/` was tracked and contained codex exec logs (`sessions/codex_bootstrap_log.md`, `sessions/codex_exec/...`); commit `67676f6` added these files.
- `.claude/skills/codex-subagent/scripts/codex_exec.py` now writes logs under `.codex/sessions/codex_exec/<human|auto>/...` by default (TTY-based classification) and accepts `CODEX_SUBAGENT_LOG_DIR` / `CODEX_SUBAGENT_LOG_SCOPE` or `--log-dir` / `--log-scope` overrides.
- `.claude/skills/codex-subagent/scripts/codex_query.py` and `codex_feedback.py` read logs under `.codex/sessions/codex_exec` by default and can filter by `--scope/--log-scope all|human|auto` (default uses `CODEX_SUBAGENT_LOG_SCOPE` when set).
- `.claude/commands/tasks/codex-subagent.md` instructs running `codex_exec.py`, which generates logs according to the configured log directory.
- `.gitignore` ignores `sessions/` (line 29), so any root `sessions/` outputs would be untracked/ignored.
- `memories/`, `cache/`, and `tools/` were not tracked in git and had no references in AGENTS/CLAUDE or `.claude` commands/skills.
- `memories/` and `cache/` were root-owned and empty; `cache/python/` was present but empty.
- `tools/` was empty and untracked.

## Solution
- `skills/` originated from commit `67676f6` as a repo copy of Codex system skills and was referenced by skill-authoring docs and lint config; those references were updated to `.codex/skills/.system`.
- `sessions/` originated from commit `67676f6` as the log output path for codex-subagent scripts; logging now defaults to `.codex/sessions/codex_exec` with override support.
- The creation sources of `memories/`, `cache/`, and `tools/` remain undocumented in repo history, AGENTS/CLAUDE, or `.claude` commands/skills.
- Top-level `skills/`, `memories/`, `cache/`, `tools/`, and `sessions/` were removed in the current cleanup.

## Verification
- `git log --name-status --oneline -- sessions skills`
- `git show --name-status --oneline 67676f6`
- `rg -n "skills/.system" .claude/skills/skill-authoring/references/agent_skills_overview.md`
- `rg -n "\\.codex/skills/\\.system" pyproject.toml`
- `rg -n "CODEX_SUBAGENT_LOG_DIR|log-dir|codex_exec" .claude/skills/codex-subagent/scripts/codex_exec.py`
- `rg -n "CODEX_SUBAGENT_LOG_DIR|log-dir|codex_exec" .claude/skills/codex-subagent/scripts/codex_query.py`
- `rg -n "CODEX_SUBAGENT_LOG_DIR|log-dir|codex_exec" .claude/skills/codex-subagent/scripts/codex_feedback.py`
