ROLE: Parent agent orchestration for AGENTS branch comparison / __TASK_ID__
DATE: 2026-03-19

OBJECTIVE
- In the worktree at `__WORKTREE__`, perform an independent confirmation run for `BUG-01`.
- Try to make the targeted local gates pass without editing outside the declared scope.

SCOPE
- Target repo: `__WORKTREE__`
- Target paths:
  - `app/sharepoint_list/internal/validators.py`
  - `app/sharepoint_list/internal/request_builders.py`
  - `tests/sharepoint_list/test_validators.py`
  - `tests/sharepoint_list/test_operations_select.py`

CONSTRAINTS
- Branch alias: `__BRANCH_ALIAS__`
- No edits outside the allowed target paths.
- No git history or external baseline references.
- No secret exposure.
- If a package CLI is unavailable, do not install tools.
- Parent will run authoritative gates after the pipeline.

REQUIRED OUTPUTS
1. `/draft` fix hypothesis and success criteria
2. `/facts` commands run, observed failures, and evidence
3. `/critique` unresolved risks or review findings
4. `/revise` actual changes made and remaining blockers

TEST DESIGN REQUIREMENT
- Favor `uv run ruff check ...` and `uv run pytest -q --no-cov ...` on the targeted files/tests.

REVIEW OUTPUT DIR
- `__OUTPUT_DIR__`
