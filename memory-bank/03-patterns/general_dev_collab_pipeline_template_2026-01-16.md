# General Dev Collaboration Pipeline Template (2026-01-16)

## Problem
- verify で追加検証が必要になった際に、改善→再検証までを自動で回す汎用パイプラインが未整備。

## Research
- ローカル設計ドキュメントと過去のパイプライン運用方針を参照し、改善ループに必要なステージとガードレールを整理。

## Solution
- draft/execute/review/revise/verify の5段構成。
- verify がループ条件を判定し next_stages で execute→review→revise→verify を再実行。
- max_loops / success / guardrails は親エージェントが自由に設定。
- オプション動的ステージとして diagnose/release を許可。
- ガードレール例: 単一行JSON、capsule_patch 1件、/facts は配列。
- 導線: `.claude/skills/general-dev-collab-pipeline` 配下にスターター/テンプレ/メタプロンプトを配置。

## Verification
- パイプライン spec / prompt / テンプレート / メタプロンプトを作成。
- ステージ責務とループ条件を文書化。

## Tags
- #pipeline #collaboration #verification-loop #general-template
