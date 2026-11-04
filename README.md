# Shared Skills

会議の議事録・残件整理と、Python PoCの開発・保守を支援する公開用Skill集です。

| 内容 | 役割 |
| --- | --- |
| `create-auditable-meeting-minutes` | 正本JSON、議事録HTML、Redmine取込JSON、検証レポートを生成 |
| `meeting-transcript-to-open-items` | 残件抽出のみを行う代替Skill |
| `redmine-meeting-orchestrator` | 議事録生成、dry-run、承認後の登録・再取得をつなぐAgent |
| `skill-creator` | Skillの作成・改善と、任意の比較評価 |
| `safe-refactoring` | 外部挙動を保った構造・可読性の改善 |
| `reverse-engineer-specification` | コード・README・UIから根拠付きの現行仕様を作成 |
| `generate-tests-from-spec` | 仕様と既存実装からケースを設計し、pytestを作成・実行 |

Redmine操作には別リポジトリ [Items](https://github.com/Yoshiaki-Ida/Items) の
`redmine-ticket-correction` が必要です。Skill単独では登録しません。

## 導入

配備にはGitとWindows / PowerShell 5.1以上を使います。SkillはGitHub CopilotまたはCodexで使用します。
議事録の生成・テストにはPython 3.11以上、議事録用AgentにはVS Code版GitHub Copilotが必要です。

```powershell
git clone https://github.com/Yoshiaki-Ida/shared-skills.git
Set-Location .\shared-skills
.\scripts\install.ps1
```

最初は差分表示だけです。対象が意図どおりなら適用します。

```powershell
.\scripts\install.ps1 -Apply
```

配備先は `~/.agents/skills/<name>/` と `~/.copilot/agents/` です。
適用してよいのは、対象が上記の6 Skill・1 Agentの自分用配備先で、表示が `NEW` または `OK` のみの場合です。
`OK` は同じ内容を意味します。UTF-8テキストのCRLF/LFだけの違いも `OK` とし、既存ファイルを保持します。
`CONFLICT` が1件でもあれば通常の適用は書き込み前に停止します。削除や無確認の更新はしないでください。
既存の別Skillや配備先固有ファイルを削除せず、旧配布用マニフェストも変更しません。
`INSTALL_PASS` が表示され、再度引数なしで実行してすべて `OK` なら完了です。

### CONFLICTがある場合

1. 通常の `-Apply` は中止します。この停止では配備ファイルは変更されません。
2. 表示された競合ファイルすべてを、同名の配布元ファイルと比較します。下記は1ファイルの比較例です。ほかの競合も確認してください。
3. 既存の個人変更を保持したい場合や差分の用途が不明な場合は、ここで停止して管理者・作成者へ相談します。
4. 全競合ファイルを公開版に置き換えてよいと判断した場合だけ、`-Apply -Update` を実行します。

```powershell
$installed = Join-Path $env:USERPROFILE '.agents\skills\create-auditable-meeting-minutes\SKILL.md'
code --diff $installed '.\skills\meeting-and-records\create-auditable-meeting-minutes\SKILL.md'
```

`code` コマンドが使えない場合はVS Codeで2ファイルを開き、エクスプローラーの「比較対象の選択」「選択項目と比較」を使います。
大文字小文字、空白、文字コードの違いはCRLF/LFだけの違いとはみなしません。

```powershell
.\scripts\install.ps1 -Apply -Update
.\scripts\install.ps1
```

更新時は、上書き対象の競合ファイルを `~/.agents/backups/shared-skills/<時刻と識別子>/` に保存・検証してから配備します。
バックアップに失敗した場合は配備を書き換えず停止します。成功時に `BACKUP:` と保存先を表示します。
`INSTALL_PASS` がない、赤いエラーが出る、再確認で `NEW` / `CONFLICT` が残る場合は先へ進まないでください。
更新中に失敗した場合もバックアップは残ります。自動復元はしないため、状態を確認してから復元します。

### 更新前に戻す場合

`$backup` に `BACKUP:` で表示された時刻付きフォルダを設定し、対応表の全項目を確認します。
確認後に復元コマンドを実行すると、そのバックアップに記録された既存ファイルだけを戻します。
新規追加ファイルや個人の追加ファイルは削除しません。復元後は旧版に戻るため、公開版との比較が再び `CONFLICT` になることがあります。

```powershell
$backup = '<BACKUPで表示されたフォルダ>'
$restore = Get-Content -LiteralPath (Join-Path $backup 'manifest.json') -Raw | ConvertFrom-Json
$restore | Format-Table Target, Backup -AutoSize
```

```powershell
$restore | ForEach-Object {
	Copy-Item -LiteralPath $_.Backup -Destination $_.Target -Force
}
```

バックアップには個人の設定・変更を含む場合があります。GitHubへ登録せず、そのまま保管してください。

## 会議で使う

Itemsをセットアップし、VS Codeで `Items` フォルダを開きます。
Agent一覧に表示されない場合はVS Codeを再読み込みしてください。
`redmine-meeting-orchestrator` を選び、文字起こしとアジェンダを添付します。

```text
このアジェンダと文字起こしから議事録とRedmine取込JSONを生成して。
```

文字起こしは `.vtt` / `.srt` / `.txt` / `.md` を使用します。音声だけでは処理しません。
`redmine-meeting-orchestrator`は専用Agentで、議事録生成に`create-auditable-meeting-minutes` Skillを使用します。
プロジェクト名を伝え、実際に取得した候補から親議事録用・子チケット用のトラッカー名を選びます。同名ならID等で確認します。既存の確認済みID指定も利用できます。
Agentは議事録に加え、登録ドラフト（dry-run）の実HTMLへのリンクを提示して停止します。例として`redmine-import-result.json`の確認用HTMLは`redmine-import-result.html`です。議事録HTMLとは別に開き、最終本文、登録先、担当者、期限、件数、設定不足を確認します。まだRedmineには登録されていません。
確認後、次の新しいメッセージで「Redmineへ登録して」と返信します。同じターンの自動承認や単なる了解では登録しません。入力・設定・接続先・候補が変われば再ドラフトと再承認が必要です。結果JSONは機械用の証跡として保持します。
名称候補の取得はGETのみの読取操作であり、登録の承認とは別です。名称は候補取得時点、担当者名は設定対応表の情報として扱います。
APIキーはチャットへ渡さず、Items側READMEのユーザー環境変数の手順に従います。
会議情報をAIへ渡せるか、事前に組織の規則を確認してください。

## 開発・保守で使う

対象のリポジトリを開き、必要な資料と作業範囲を渡します。

| Skill | 入力と依頼例 |
| --- | --- |
| `skill-creator` | 用途と期待出力を渡し、「この作業をSkill化して」 |
| `safe-refactoring` | 対象コードと確認手段を渡し、「挙動を保って構造を整理して」 |
| `reverse-engineer-specification` | 対象コードを渡し、「現行仕様を根拠付きで起こして」 |
| `generate-tests-from-spec` | 仕様書と対象コードを渡し、「この仕様のpytestを整備して」 |

Python作業は対象プロジェクトの既存環境を使います。外部サービスは模擬化し、試験用データを隔離します。
不明点の確認、実行範囲、正式仕様の承認条件は各Skillのローカル差分に記載しています。

### 原文と独自差分

各Skillは公開版の原文、`references/local-tailoring.md`、出典記録を分けています。
固定コミットとハッシュは各`references/upstream-provenance.json`に記録しています。

| Skill | 土台とライセンス |
| --- | --- |
| `skill-creator` | [Anthropic原文](skills/skill-management/skill-creator/references/anthropic-skill-creator.md)、[ライセンス](skills/skill-management/skill-creator/LICENSE.txt) |
| `safe-refactoring` | [GitHub refactor原文](skills/software-development/safe-refactoring/references/upstream.md)、[ライセンス](skills/software-development/safe-refactoring/LICENSE.upstream.txt) |
| `reverse-engineer-specification` | [GitHub doc-and-modernize原文](skills/software-development/reverse-engineer-specification/references/upstream.md)、[ライセンス](skills/software-development/reverse-engineer-specification/LICENSE.upstream.txt) |
| `generate-tests-from-spec` | [spec-forge原文](skills/software-development/generate-tests-from-spec/references/upstream.md)、[ライセンス](skills/software-development/generate-tests-from-spec/LICENSE.upstream.txt) |

Skill作成の形式検証にはPyYAMLを使います。Anthropic由来の実AI比較ツールにはClaude CLIと認証が必要です。
比較評価は任意です。Codex/Copilotでの評価結果と区別し、費用・実行条件を確認してから実行します。

## テスト

Itemsと本リポジトリを同じ親フォルダへ配置し、pytestとPyYAMLを利用できるItemsのPython環境で実行します。
配置が異なる場合は`ITEMS_APP_ROOT`へRedmineアプリのルートを指定します。

```powershell
..\Items\redmine-ticket-correction\.venv\Scripts\python.exe -m pytest -q .\tests
```

議事録生成、dry-run、模擬APIへの登録と再エクスポート、隔離した配備先へのインストールを検証します。
4件の追加Skillは、原文のハッシュ、参照先、形式検証、AIを呼ばない補助ツールの起動も確認します。
同梱例は架空の会議です。実Redmineの登録と実会議でのAgent抽出精度は別途確認してください。
社内向け資料、実会議、接続設定、APIキーは含めません。
