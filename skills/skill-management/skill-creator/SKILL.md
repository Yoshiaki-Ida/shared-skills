---
name: skill-creator
description: Anthropic版を基にAgent Skillを作成・改善し、必要に応じて旧版やSkillなしとの比較評価を行う。GitHub CopilotとCodexで使うSkillの新規作成、見直し、発動条件の調整に使用する。共有原本・一覧・配置と質問ゲートはローカル差分に従う。
metadata:
  upstream: anthropics/skills
  upstream-commit: ca45fc496a3436251f191354091d557da31c15b5
  tailoring: references/local-tailoring.md
---

# Skill Creator — Anthropicベースのテーラリング版

作成・比較評価・改善の基本手順はAnthropic版を使う。独自の運用ルールは差分ファイルだけで管理する。

1. [ローカル差分](references/local-tailoring.md)を読む。依頼範囲・確認条件・実行環境を先に確認する。
2. [Anthropic原文](references/anthropic-skill-creator.md)を読み、現在の作成／改善段階から進める。原文中の相対パスとコマンドの作業ディレクトリは、このSkillのルートを基準とする。
3. 原文とローカル差分が衝突する部分だけ、ローカル差分を適用する。システム・開発者・ユーザーの指示を優先する。

評価・補助スクリプトは原文に対応するものを同梱している。インストール・外部CLI評価・コミット・公開を、このSkillの作成依頼だけで実行しない。

取得元・固定コミット・18ファイルのハッシュは[出典記録](references/upstream-provenance.json)を参照する。上流由来のライセンスは[LICENSE.txt](LICENSE.txt)に保持する。上流原文・補助ファイルは自動更新せず、更新時にローカル差分との整合を確認する。
