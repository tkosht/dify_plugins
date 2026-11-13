# Dify Plugins Project

Dify Plugins プロジェクト


## Plugins 一覧

- sharepoint_list プラグイン


## プラグインの作者名と既存ワークフロー

現在のソースでは、5プラグインの作者名を `agen-i` に統一しています。Difyは作者名・プラグイン名・版を識別に使うため、`tkosht` からの変更は名前空間の移行にあたります。同じ名前・版でも、既存プラグインの通常更新として扱わないでください。

`docs/dsl/SharepointAgent.yml` と `docs/dsl/SharepointListBot.yml` は `tkosht/sharepoint_list` を使った既存の参考DSLです。後者には0.0.5と0.0.1のハッシュ付き識別子が混在しており、現在のソースから作る配布物の識別子ではありません。`agen-i` の配布物を導入した後は、Difyの画面でツールと認証情報を選び直し、動作を確認してからDSLを再エクスポートしてください。作者名だけを置き換えて既存のハッシュを流用することはできません。

PDFプラグインの導入と名前空間移行の条件は [導入手順](app/pdf_text_pages/README.md#導入) を参照してください。
