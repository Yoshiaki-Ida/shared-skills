---
name: safe-refactoring
description: GitHubのrefactorを基に、既存PoCの外部挙動を保ちながら構造・可読性・保守性を改善する。関数分割、命名、重複整理、パス・importの修正に使用する。変更範囲、Git操作、検証はローカル差分に従う。
metadata:
  upstream: github/awesome-copilot
  upstream-skill: refactor
  upstream-commit: edbecfa9099c4addae1f500cca1ac067204b30fd
---

# 安全なリファクタリング

1. [ローカル差分](references/local-tailoring.md)を読み、変更範囲と実行条件を確認する。
2. [公開版の原文](references/upstream.md)に従い、該当するリファクタリング手順を使う。衝突する部分はローカル差分を適用する。

原文中の参照先は、このSkillのルートを基準とする。取得元・固定版・ハッシュは[出典記録](references/upstream-provenance.json)、上流のライセンスは[LICENSE.upstream.txt](LICENSE.upstream.txt)で管理する。
