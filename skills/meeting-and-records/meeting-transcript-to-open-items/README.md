# meeting-transcript-to-open-items

会議アジェンダと文字起こしから、決定事項・対応事項・指摘事項・未決事項・確認事項・保留事項をJSONへ整理するGitHub Copilot Agent Skill案です。

レビュー会議専用ではなく、一般会議、進捗会議、顧客打合せ、課題検討会にも使えます。

```text
アジェンダ + Teams文字起こし
↓
JSON生成
↓
JSON Schema検証
↓
Markdown回覧資料生成
↓
参加者確認
↓
必要な残件だけチケット化
```

特に、指摘らしい発言があっても結論が出ていない場合は `unresolved` として残します。


## v5追加点

- `investigation` を追加し、調査と修正を分離
- 話者名不明時の `assignee_speaker_id` を追加
- 議論経緯を `discussion_summary` へ保持
- 結論反転を `superseded_conclusions` へ保持
- 同一論点の再登場を統合し、曖昧時は `possible_duplicate_of`
- ASR誤認識候補を `normalized_terms` へ保持
- Teams生文字起こし向けの意地悪テストケースを追加

## 追加ファイル

- `adversarial-test-cases.json`


## v6追加点

- 発言にない確認事項・アクションの捏造を禁止
- 「したい」「考えている」を実施合意として扱わない
- 運営連絡を原則として残件化しない
- `missing_information` を必要最小限へ制限
- 出席者、欠席言及、その他言及人物を分離
- 各項目に `source_grounding` を追加
- `explicit` 以外の追跡項目は人間確認または除外
- TC-18〜TC-24を追加し、過剰抽出と創作を回帰試験化

## v7追加点

- 会議全体の要旨を `meeting_summary` としてJSON正本へ追加
- `overview`、`main_topics`、`key_outcomes`、`open_points`、`next_step_summary` を保持
- 個々のチケット要約とは別に、会議全体の流れと着地点を俯瞰可能にした
- `meeting_summary` から新しい対応事項や確認事項を生成することは禁止
- Markdown回覧資料にも「会議全体の要旨」セクションを追加
- TC-25〜TC-28で、要旨生成、捏造防止、次アクション未明示時の `null`、itemsとの整合を回帰試験化

## v7位置づけ

v7では、個々のチケット情報に加えて、会議全体を俯瞰する `meeting_summary` を正式機能として統合した。

JSON Schema、Skill本文、Markdownテンプレート、README、回帰テストを同一パッケージで管理する。


## v8追加点

- Redmine会議・DR/CR親チケット用の `redmine_meeting_fields` をSchemaへ追加
- 各残件にRedmine子チケット用の `redmine_issue_fields` を追加
- Redmine上の項目名称をJSONキーへそのまま採用
- JSONでは全項目を必須とし、取得不能・非該当は `null` または `[]`
- Markdownでは値が存在するRedmine項目だけを表示
- `完了` は独立フィールドではなく、`ステータス` または `判定` の値として整理
- 手動指摘件数とAI抽出件数を混同しないルールを追加
- 途中案を最終決定として早取りしない回帰テストを追加

## v9追加点

- 子チケットの標準内容欄とRedmine専用項目の役割を明確化
- `description` は「内容:」ラベルを付けず、内容欄へ本文として直接記載
- `rationale` と `expected_state` は内容欄の「理由・背景」「期待状態」として保持
- `action_plan` をRedmine項目 `処置内容` へ転記
- `completion_criteria` を改行区切りでRedmine項目 `確認内容` へ転記
- `next_review_timing` は絶対日付を確定できる場合だけRedmine項目 `確認日` へ転記
- 子チケット内容欄への重複記載を禁止
- ITEM ID、種別、チケット化判定、発言根拠レベル等の内部情報を通常の内容欄へ表示しない
- 子チケットをAI分析レポートではなく、担当者向けの作業票として簡潔化
- TC-34〜TC-37で転記先、重複防止、確認日の捏造防止を回帰試験化
