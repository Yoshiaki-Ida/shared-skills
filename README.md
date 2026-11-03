# Shared Skills

会議の文字起こしから議事録と残件を整理する、GitHub Copilot向けの公開用Skill集です。

| 内容 | 役割 |
| --- | --- |
| `create-auditable-meeting-minutes` | 正本JSON、議事録HTML、Redmine取込JSON、検証レポートを生成 |
| `meeting-transcript-to-open-items` | 残件抽出のみを行う代替Skill |
| `redmine-meeting-orchestrator` | 議事録生成、dry-run、承認後の登録・再取得をつなぐAgent |

Redmine操作には別リポジトリ [Items](https://github.com/Yoshiaki-Ida/Items) の
`redmine-ticket-correction` が必要です。Skill単独では登録しません。

## 導入

Git、Windows / PowerShell 5.1以上、Python 3.11以上、VS Code版GitHub Copilotが必要です。

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
同名ファイルが異なる場合は、書き込み前に停止します。
差分を確認して置き換えを承認した場合だけ `-Apply -Update` を指定します。
既存の別Skillや配備先固有ファイルを削除せず、旧配布用マニフェストも変更しません。
再度引数なしで実行し、すべて `OK` なら配備内容は一致しています。

## 使用

Itemsをセットアップし、VS Codeで `Items` フォルダを開きます。
Agent一覧に表示されない場合はVS Codeを再読み込みしてください。
`redmine-meeting-orchestrator` を選び、文字起こしとアジェンダを添付します。

```text
このアジェンダと文字起こしから議事録とRedmine取込JSONを生成して。
```

文字起こしは `.vtt` / `.srt` / `.txt` / `.md` を使用します。音声だけでは処理しません。
プロジェクト識別子と親子トラッカーIDを確認します。
Agentは議事録とdry-runを提示して停止します。確認後、別メッセージで「Redmineへ登録して」と返信します。
入力や接続先が変われば再度dry-runと承認が必要です。
APIキーはチャットへ渡さず、Items側READMEのユーザー環境変数の手順に従います。
会議情報をAIへ渡せるか、事前に組織の規則を確認してください。

## テスト

Itemsと本リポジトリを同じ親フォルダへ配置し、ItemsのPython環境で実行します。

```powershell
..\Items\redmine-ticket-correction\.venv\Scripts\python.exe -m pytest -q .\tests
```

議事録生成、dry-run、模擬APIへの登録と再エクスポート、隔離した配備先へのインストールを検証します。
同梱例は架空の会議です。実Redmineの登録と実会議でのAgent抽出精度は別途確認してください。
社内向け資料、実会議、接続設定、APIキー、他の業務Skillは含めません。