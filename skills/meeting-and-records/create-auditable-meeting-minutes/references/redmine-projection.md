# Redmine投影仕様

## 目次

1. 出力責務
2. 親チケット
3. 子チケット
4. チケット化判定
5. 実行手順

## 出力責務

正本JSONは会議記録の全情報を保持する。`redmine-import.json`は既存の`redmine-ticket-correction`へ渡す派生物とする。Redmine固有の制約を理由に正本から議論経緯、異議、証跡を削除しない。

## 親チケット

以下を親チケットの`meeting_summary`へ投影する。

- `meeting_summary` → `overview`
- `agenda_items[].title` → `main_topics`
- `decisions[].statement`と`action_items[].action` → `key_outcomes`
- `open_items[].statement` → `open_points`
- 対応内容と次の判断方法 → `next_step_summary`

以下を`redmine_meeting_fields`へ投影する。

- `document_control.document_id` → `議事録番号`
- `meeting.source_documents` → `対象ドキュメント番号・表題`
- `meeting.start_at` → `実施日`、`実施時間(開始)`
- `meeting.end_at` → `実施時間(終了)`
- `meeting.location` → `実施場所`
- `meeting.participants` → `出席者_テキスト_`、`出席者`
- `document_control.approval_status` → `判定`

Redmine環境の選択肢と一致する保証がない項目は、適用前のdry-runで確認する。

## 子チケット

### 対応事項

`action_items[]`を`items[type=action_item]`へ変換する。

- `action` → `title`、`description`、`action_plan`、`処置内容`
- `owner` → `assignee`、`担当者`
- `due_date` → `due_date`、`期日`
- `completion_criteria` → `completion_criteria[]`、`expected_state`、`確認内容`
- 対応元議題 → `discussion_summary`、`rationale`
- `evidence` → `evidence`

### 未決事項

`open_items[]`を`items[type=unresolved]`へ変換する。

- `statement` → `title`、`description`
- `reason_open` → `rationale`
- `next_decision_method` → `action_plan`、`処置内容`
- `owner` → `assignee`、`担当者`
- `target_date` → `due_date`、`期日`

### 決定事項

`decisions[]`は親チケットの要旨へ含め、子チケットへ変換しない。決定に伴う作業がある場合は、正本の`action_items[]`として独立していることを確認する。

## チケット化判定

- 担当者、期限、完了条件が揃う対応事項は`ready`
- いずれかが欠ける対応事項は`conditionally_ready`
- 内容のある未決事項は`conditionally_ready`
- 内容のない項目は`not_ready`

不足値を推測で埋めない。Redmineの担当者名からIDへの変換は`redmine-ticket-correction`の設定に委ねる。

## 実行手順

```powershell
python scripts/render_minutes_outputs.py .\minutes-source.json --output-dir .\output
```

次を確認する。

1. `validation-report.json`の`valid`が`true`
2. `blocking_review_flag_ids`が空、または人間が内容を把握している
3. HTMLの決定、対応、未決事項が正本と一致
4. `redmine-import.json`の子チケット件数が対応事項数＋未決事項数と一致
5. `redmine-ticket-correction`をdry-runで実行し、未解決の担当者・選択肢・日付を確認
