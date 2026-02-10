# Repo Baseline Parity Evaluation

## Objective
- 新規または大幅改修pluginを既存baselineと比較し、完成度を定量評価する。

## Baseline selection rule
1. 同じpluginタイプの既存実装を1つ選ぶ。
2. 選定根拠を記録する。
3. 例: OpenAI Responses provider は `app/openai_gpt5_responses` をbaselineにする。

## Comparison commands
```bash
diff -rq app/<baseline_plugin> app/<target_plugin>
diff -rq tests/<baseline_plugin> tests/<target_plugin>
```

## Scoring dimensions (100 points)
1. Interface contract parity: 30点
2. Runtime behavior parity: 30点
3. Test depth and reproducibility: 25点
4. Release readiness (package/install): 10点
5. Documentation and distribution files: 5点

## Pass/fail rule
1. 合計80点以上を合格目安とする。
2. `Release readiness` が0点なら総合点に関係なく不合格。
3. 必須補助ファイル欠落は不合格。
4. 比較結果に重大差分がある場合は理由を明記する。

## Reporting template
1. Baseline / Target path
2. Score breakdown
3. Critical gaps
4. Required follow-up actions
