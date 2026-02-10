# Generic Baseline Parity Evaluation

## Objective
- 任意リポジトリで新規/改修pluginの完成度を既存baselineと比較して判定する。

## Baseline selection rule
1. 同タイプの既存pluginを1つ選ぶ。
2. 選定理由を記録する。
3. 比較対象は実装とテストの両方を揃える。

## Comparison commands
```bash
diff -rq <baseline-plugin-path> <target-plugin-path>
diff -rq <baseline-test-path> <target-test-path>
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
4. 重大差分がある場合は修正方針を併記する。

## Reporting template
1. Baseline / Target path
2. Score breakdown
3. Critical gaps
4. Required follow-up actions
