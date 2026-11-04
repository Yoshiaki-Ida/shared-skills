---
name: reverse-engineer-specification
description: GitHubのdoc-and-modernizeの文書化手順を基に、現行PoCのコード・README・UI・テストから要求仕様を逆起こしする。仕様の欠落・陳腐化への対応と、保守・テストの根拠作成に使用する。確認済みと推定を分け、要求仕様の項目はローカル差分に従う。
metadata:
  upstream: github/awesome-copilot
  upstream-skill: doc-and-modernize
  upstream-commit: edbecfa9099c4addae1f500cca1ac067204b30fd
---

# 仕様書の逆起こし

1. [ローカル差分](references/local-tailoring.md)で対象・成果物・確認の境界を確認する。
2. [公開版の原文](references/upstream.md)のDocumentation modeを使い、現行実装から根拠を集める。要求仕様へまとめる際はローカル差分の出力項目を適用する。

原文中の参照先は、このSkillのルートを基準とする。取得元・固定版・ハッシュは[出典記録](references/upstream-provenance.json)、上流のライセンスは[LICENSE.upstream.txt](LICENSE.upstream.txt)で管理する。
