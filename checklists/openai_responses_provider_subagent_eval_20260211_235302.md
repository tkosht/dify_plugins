# OpenAI Responses Provider Subagent Eval Checklist (20260211_235302)

- [x] 1. Create isolated workspace
- [x] 2. Define anti-cheat constrained task spec
- [x] 3. Run subagent in isolated workspace
- [x] 4. Collect subagent output JSON
- [x] 5. Run parent authoritative gates (ruff/package/pytest/diff/wc)
- [x] 6. Run anti-cheat evidence checks (absence/history/leakage)
- [x] 7. Generate reproducible runtime evidence (abstract/chunk/payload/integration)
- [x] 8. Build SHA256SUMS and verify integrity
- [x] 9. Produce parity evaluation report
