# GPT-5 Plugin Security Audit Flask Waiver (2026-03-08)

date: 2026-03-08
scope:
  - .github/workflows/ci.yml
  - .github/workflows/test-all-subsystems.yml
  - app/openai_gpt5_responses
  - app/gpt5_agent_strategies
tags: dify-plugin, pip-audit, flask, cve-2026-27205, github-actions, ripgrep

## Problem
- GitHub Actions `Run security audits` が `pip-audit` で fail した。
- 対象 PR: `task/plugin-timeout-ui` / PR #33
- 失敗内容:
  - `app/openai_gpt5_responses/requirements.txt`
  - resolved package: `flask 3.0.3`
  - vulnerability: `CVE-2026-27205`
- 同じ workflow 内で `rg: command not found` の runner 依存ノイズも発生していた。

## Research
- Actions log:
  - `CI / test (3.11) / Run security audits`
  - `Found 1 known vulnerability in 1 package`
  - `flask 3.0.3   CVE-2026-27205 3.1.3`
- Local dependency reproduction:
  - `dify-plugin==0.7.1` installs `Flask~=3.0.3`
  - `dify-plugin==0.7.2` also installs `Flask~=3.0.3`
- Upstream source check:
  - `langgenius/dify-plugin-sdks` `python/pyproject.toml`
  - current upstream still declares `Flask~=3.0.3`
- Local verification:
  - `uvx --python 3.11 --with pip-audit pip-audit --ignore-vuln CVE-2026-27205 -r app/openai_gpt5_responses/requirements.txt`
    - `No known vulnerabilities found, 1 ignored`
  - `uvx --python 3.11 --with pip-audit pip-audit --ignore-vuln CVE-2026-27205 -r app/gpt5_agent_strategies/requirements.txt`
    - `No known vulnerabilities found, 1 ignored`
  - `uvx --python 3.11 --with bandit bandit -q -r app/openai_gpt5_responses app/gpt5_agent_strategies -x tests`
    - exit code `0`

## Solution
- CI workflows では `CVE-2026-27205` を `pip-audit --ignore-vuln` で一時除外する。
- `Run security audits` は次の 3 step に分割する。
  - `Audit openai_gpt5_responses dependencies`
  - `Audit gpt5_agent_strategies dependencies`
  - `Run bandit`
- `rg` 利用前に `ripgrep` を install して、GitHub-hosted runner でも同じ policy check を安定動作させる。

## Removal Criteria
- `dify-plugin` upstream が Flask fix を含む release を出し、
  `dify-plugin` 経由で `Flask~=3.0.3` が解消されたことを確認したら、
  workflow から `--ignore-vuln CVE-2026-27205` を撤去する。

## Notes
- 今回の waiver は `CVE-2026-27205` 1 件に限定する。
- `dify-plugin` の fork / vendor 化は実施していない。
