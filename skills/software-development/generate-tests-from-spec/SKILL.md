---
name: generate-tests-from-spec
description: spec-forgeのテストケース設計を基に、要求仕様と既存実装から正常系・異常系・境界値・回帰の観点を整理し、pytestを作成・実行する。仕様のあるPoCのテスト整備に使用する。既存ケースの再利用、隔離したデータ、外部APIの模擬化と実行範囲はローカル差分に従う。
metadata:
  upstream: tercel/spec-forge
  upstream-skill: test-cases-generation
  upstream-commit: 004e80a3cd5411d7717a1185eb345fafade5555d
---

# 仕様書からテストを生成する

1. [ローカル差分](references/local-tailoring.md)で仕様・テスト実装・実行範囲を確認する。
2. [公開版の原文](references/upstream.md)のSpec Modeでテストケースを設計する。原文の参照資料を使い、続けてローカル差分に従いpytestを実装・実行する。

`references/*`はこのSkillのルート、原文の`@../shared/*`は`references/upstream-shared/*`へ対応する。取得元・固定版・ハッシュは[出典記録](references/upstream-provenance.json)、上流のライセンスは[LICENSE.upstream.txt](LICENSE.upstream.txt)で管理する。
