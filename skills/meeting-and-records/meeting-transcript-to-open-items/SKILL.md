---
name: meeting-transcript-to-open-items
description: 会議アジェンダと文字起こしから、合意済みの決定、対応、調査、指摘、未決事項だけを論点単位の残件JSONへ抽出する。一般会議、進捗会議、レビュー会議、顧客打合せで、会議後の追跡項目だけを整理する場合に使用する。正式な議事録本文、監査用承認証跡、HTMLやRedmine派生成果物まで必要な場合は使用しない。
---

# 会議文字起こしから決定事項・残件を整理するスキル

## 不明点の判断ゲート

- 不明点・判断不能点のうち、結果、対象範囲、安全性、データ更新、成果物の種類・形式・内容に影響するものは、依存する処理を始める前にユーザーへ具体的に質問し、回答を待つ。
- 不明点を理由に終了するだけにせず、判明済み事項、不明事項、必要な回答を示し、回答後は中断地点から再開する。
- 既存仕様、明示済みルール、確認済み入力、定義済みの既定値から一意に決まる単なる実装詳細は質問せず進める。
- 質問せずに推測、代替、フォールバック、対象会議の変更、成果物の省略を行わない。
- このSkillで定義された `null`、`unknown`、`missing_information`、低confidenceは正規の出力仕様として扱う。ただし、それにより依頼された成果物や対象範囲が変わる場合は質問する。

## 目的

レビュー会議に限定せず、会議アジェンダと文字起こしから、会議後に追跡すべき情報を整理する。

対象:
- 一般会議
- 進捗会議
- 設計・仕様打合せ
- レビュー会議
- 顧客打合せ
- 定例会議
- 課題検討会

## 抽出区分

- `decision`: 決定事項
- `action_item`: 対応事項
- `investigation`: 調査事項
- `finding`: 指摘事項
- `unresolved`: 未決事項
- `confirmation`: 確認事項
- `hold`: 保留事項
- `no_action`: 対応不要
- `information`: 共有事項
- `question`: 質問
- `small_talk`: 雑談
- `undetermined`: 判定不能

## 基本方針

1. 発言単位ではなく、アジェンダまたは論点単位でまとめる。
2. 会話途中の意見ではなく、最終的な着地点を優先する。
3. 指摘らしい発言があっても、対応要否が未確定なら `unresolved` とする。
4. 決定事項、対応事項、調査事項を分ける。
5. 担当者、期限、完了条件を推測しない。話者名が不明な場合は話者IDだけを残す。
6. 対応不要になった事項を残件化しない。
7. 根拠発言を残す。
8. JSONを正本とし、MarkdownはJSONから生成する。
9. 人間確認前にRedmineやJiraへ登録しない。
10. 会議内容から合理的に必要と思われる作業でも、実施・確認・検討する旨が明示されていなければ項目化しない。
11. 「したい」「考えている」「話していきたい」は意向であり、実施合意として扱わない。
12. 運営連絡や一般案内を残件化しない。
13. `missing_information` は既存残件を成立させるために必要な不足だけを記録し、「あると親切」な情報を追加しない。
14. Redmine連携候補は、会議親チケット用の `redmine_meeting_fields` と、残件子チケット用の `redmine_issue_fields` に分離する。
15. Redmine項目はJSONではSchema定義分をすべて出力し、取得不能・非該当は `null`、配列項目は `[]` とする。
16. MarkdownではRedmine項目のうち、値が存在する項目だけを表示する。
17. Redmine画面上の「完了」は独立フィールドではなく、`ステータス` または `判定` の値として扱う。

18. 個々の項目とは別に、会議全体の要旨を `meeting_summary` として作成する。
19. `meeting_summary` は文字起こしと `items` の俯瞰であり、新しい対応事項・確認事項・次アクションを生やしてはならない。



## 追跡項目として抽出するためのゲート

項目化する前に、以下のいずれかが会議内で明示されているか確認する。

1. 決定された
2. 誰かが実施すると合意した
3. 調査または確認が必要と合意した
4. 未決事項として持ち越すと合意した
5. 問題または指摘として対応が必要と合意した

どれにも該当しない場合は、原則として追跡項目へしない。

追跡項目へ昇格しない例:

- 単なる提案
- 一般論
- 推奨行動
- 善意による補完
- 「必要そう」という推測
- 「したい」「考えている」という意向
- 会議運営上の案内
- 不在者への一般的な連絡依頼
- その場で解消した質問
- 感想だけで終わった内容

各候補について、次を自問する。

> この項目は、会議参加者が本当に追跡すると合意したか。

明確に「はい」でなければ、`information` または抽出対象外とする。

## 捏造防止ルール

以下を禁止する。

- 発言にない担当者、期限、確認作業、会議開催を作る
- 発言にない連絡チャネル、連絡期限、完了条件を作る
- 欠席者への共有要否を勝手に確認事項へする

例:

```text
別でちょっと話していきたいと思っています
```

正しい扱い:

```json
{
  "discussion_summary": "別途話を続けたい意向が示された。",
  "action_plan": null,
  "next_review_timing": null
}
```

誤った扱い:

```json
{
  "action_plan": "別途検討会を開催する"
}
```


## Teams生文字起こしへの耐性

文字起こしは整理済み議事録ではなく、生データとして扱う。

想定するノイズ:

- 話者名が `話者1`、`話者2` のみ
- 発言が途中で切れる
- 同じ論点が後半で再登場する
- 途中結論が後から覆る
- 宿題が後で取り消される
- 技術用語や製品名のASR誤認識
- 雑談と本題の混在
- 複数論点の混線

### 話者の扱い

人名が取れない場合は、推測で実名を補わず `speaker_id` を保持する。

```json
{
  "assignee": null,
  "assignee_speaker_id": "話者2"
}
```

人名が取れる場合でも、文字起こし由来の話者IDがあるなら両方保持してよい。

### 最終結論の優先

同じ論点で結論が変化した場合、最後に合意された内容を現行結論とする。

例:

```text
修正する
↓
再検討
↓
現行仕様で問題なし
```

最終結果:

```json
{
  "type": "no_action",
  "superseded_conclusions": [
    "当初は修正する方針だった"
  ]
}
```

途中結論は削除せず、`superseded_conclusions` に要約して残す。

### 同一論点の再登場

同じ論点が会議後半で再登場しても、別項目として重複登録しない。

統合判断には以下を使う。

- 対象
- 機能または成果物
- 問題内容
- 技術用語
- アジェンダ
- 根拠発言
- 最終結論

同一論点の可能性が高いが断定できない場合は、`possible_duplicate_of` に候補IDを記録し、人間確認へ回す。

### ASR誤認識

技術用語、製品名、略語、人名は誤認識される可能性がある。

補正時は原文を失わず、候補と確信度を保持する。

```json
{
  "normalized_terms": [
    {
      "raw": "ピーエルシー",
      "normalized": "PLC",
      "confidence": "high"
    }
  ]
}
```

推測に近い補正は確定せず、`confidence: "low"` として人間確認対象にする。



## 参加者・欠席者・言及人物の扱い

文字起こしに登場した人名を、すべて参加者として扱わない。

- `participants`: 発言記録、招集情報、参加者一覧などから出席が確認できる人物
- `absent_people_mentioned`: 欠席者として言及された人物
- `mentioned_people`: 会話中に名前だけ登場した人物

発言がなく、欠席として言及された人物は `participants` に入れない。
参加状況に確証がない場合は `attendance_status: "unknown"` とし、人間確認へ回す。



## 会議全体の要旨

個々の `items` とは別に、会議全体を俯瞰するための `meeting_summary` を生成する。

```json
{
  "meeting_summary": {
    "overview": "会議全体の簡潔な要旨",
    "main_topics": [
      "主な議題"
    ],
    "key_outcomes": [
      "明示的に決まったこと、実施・調査すると合意したこと"
    ],
    "open_points": [
      "未決事項、確認待ち、調査中の論点"
    ],
    "next_step_summary": "会議内で明示された次の進め方。明示がなければnull"
  }
}
```

各項目の役割:

- `overview`: 会議全体で何を議論し、どこまで決まったかを短くまとめる
- `main_topics`: 会議で扱った主要論点
- `key_outcomes`: 決定、対応、調査など、会議内で明示された成果
- `open_points`: 会議終了時点で残った未決、確認待ち、調査中の論点
- `next_step_summary`: 会議全体として明示された次の進め方。根拠がなければ `null`

禁止事項:

- 欠席者がいることだけを根拠に「共有する」「連絡する」を追加しない
- 意向表明から「別途会議を開催する」などを生成しない
- `items` に存在しない新しい対応事項を `key_outcomes` へ追加しない
- 決定済み事項を `open_points` に残さない
- 明示されていない次アクションを `next_step_summary` に補完しない

`meeting_summary` はチケット候補の生成領域ではない。
文字起こしと `items` を、人間が短時間で理解するための会議単位の要約である。



## Redmine連携候補

将来のRedmine API連携を考慮し、会議そのものと個々の残件を分離する。

- `redmine_meeting_fields`: 会議・DR/CR親チケット用
- `items[].redmine_issue_fields`: 残件子チケット用

### JSON出力原則

Schemaに定義されたRedmine項目は、該当しない場合も省略しない。

- 文字列・数値項目: `null`
- 複数選択項目: `[]`

値がないことを理由にプロパティ自体を削除してはならない。
また、空欄のRedmine項目をすべて `missing_information` へ追加してはならない。
`missing_information` は、成立済み残件の実行または判定に不可欠な不足だけを保持する。

### 会議親チケット用項目

```json
{
  "redmine_meeting_fields": {
    "ステータス": null,
    "優先度": null,
    "担当者": null,
    "対象バージョン": null,
    "開始日": null,
    "期日": null,
    "進捗率": null,
    "開発項目": null,
    "機能区分": null,
    "開催回数": null,
    "議事録番号": null,
    "工程": null,
    "方式": null,
    "対象ドキュメント番号・表題": null,
    "実施日": null,
    "実施時間(開始)": null,
    "実施時間(終了)": null,
    "DR/CR時間": null,
    "DR/CR工数(書面審議時)": null,
    "実施場所": null,
    "出席者(選択)_": [],
    "出席者(テキスト)_": null,
    "レビューア数": null,
    "DR対象頁数・ライン数(L)・項目数": null,
    "全体頁数・ライン数(L)・項目数": null,
    "手動指摘件数": null,
    "手動": null,
    "DRチェッカー": null,
    "_2_品質特性": null,
    "判定": null,
    "判定理由": null,
    "出席者": null
  }
}
```

`完了` は独立した項目名として出力しない。たとえば `ステータス: 完了` または `判定: 完了` として保持する。

### 残件子チケット用項目

各 `items` に以下を追加する。

```json
{
  "redmine_issue_fields": {
    "ステータス": null,
    "優先度": null,
    "担当者": null,
    "対象バージョン": null,
    "開始日": null,
    "期日": null,
    "進捗率": null,
    "開発項目": null,
    "機能区分": null,
    "工程": null,
    "方式": null,
    "対象ドキュメント番号・表題": null,
    "処置内容": null,
    "確認内容": null,
    "確認日": null,
    "_2_品質特性": null,
    "判定": null,
    "判定理由": null
  }
}
```


### Redmine子チケットの転記先

子チケットでは、情報を一つの内容欄へ詰め込まず、Redmineの標準欄・専用項目へ役割を分ける。

| itemの項目 | Redmine転記先 | 転記ルール |
|---|---|---|
| `description` | 標準の内容欄 | 本文として直接記載する。「内容:」という重複ラベルを付けない |
| `rationale` | 標準の内容欄 | `理由・背景` として記載する |
| `expected_state` | 標準の内容欄 | `期待状態` として記載する |
| `action_plan` | `redmine_issue_fields.処置内容` | 内容欄へ重複記載しない |
| `completion_criteria` | `redmine_issue_fields.確認内容` | 各条件を改行区切りで連結する |
| `next_review_timing` | `redmine_issue_fields.確認日` | 絶対日付を確定できる場合だけ `YYYY-MM-DD` で設定する |
| `assignee` | `redmine_issue_fields.担当者` | 明示された担当者だけを設定する |
| `due_date` | `redmine_issue_fields.期日` | 発言または入力情報に根拠がある値だけを設定する |
| `priority` | `redmine_issue_fields.優先度` | Redmineとの対応表がある場合だけ設定する |

#### 内容欄の構成

子チケットの標準内容欄は、原則として以下だけで構成する。

```text
descriptionの本文

理由・背景:
rationale

期待状態:
expected_state
```

- `description` の前に `内容:` を付けない。
- 値がない `理由・背景`、`期待状態` は表示しない。
- `action_plan`、`completion_criteria`、`next_review_timing` は内容欄へ重複記載しない。
- `ITEM ID`、`type`、`ticket_readiness`、`source_grounding` はJSON内部で保持するが、通常の内容欄へ表示しない。
- `evidence`、`discussion_summary`、`missing_information` はJSONおよび親議事録で保持し、子チケットの通常内容欄へ自動展開しない。
- 子チケットはAIの分析レポートではなく、担当者が処置・確認するための作業票として簡潔にする。

#### 処置内容

`action_plan` が存在する場合、その内容を `redmine_issue_fields.処置内容` に設定する。

```json
{
  "action_plan": "今週中に修正案を見直し、参加者へチャットで共有する。",
  "redmine_issue_fields": {
    "処置内容": "今週中に修正案を見直し、参加者へチャットで共有する。"
  }
}
```

発言にない処置を補完してはならない。

#### 確認内容

`completion_criteria` が存在する場合、各要素を改行区切りで連結し、
`redmine_issue_fields.確認内容` に設定する。

```json
{
  "completion_criteria": [
    "修正案がチャットで共有されている。",
    "次回会議で叩き台として扱える内容になっている。"
  ],
  "redmine_issue_fields": {
    "確認内容": "修正案がチャットで共有されている。\n次回会議で叩き台として扱える内容になっている。"
  }
}
```

`completion_criteria` が空配列の場合は `確認内容: null` とする。

#### 確認日

`next_review_timing` に会議日時等から確定できる絶対日付がある場合だけ、
`redmine_issue_fields.確認日` へ `YYYY-MM-DD` 形式で設定する。

```json
{
  "next_review_timing": "2026-07-30の定例会議",
  "redmine_issue_fields": {
    "確認日": "2026-07-30"
  }
}
```

以下のような相対表現だけでは日付を推測しない。

- 次回会議
- 2週間後
- 今週中
- 復帰後
- 修正案共有後

絶対日付へ確定できない場合は `確認日: null` とし、原文は `next_review_timing` に保持する。


### 値の設定ルール

- 会議メタデータ、アジェンダ、文字起こし、入力資料に根拠がある値だけを設定する。
- Redmineの選択肢や列挙値との対応表がない場合、勝手に正規化しない。
- `優先度: 通常`、`ステータス: 完了` などを既定値として自動入力しない。
- `出席者(選択)_` はRedmine選択肢との一致が確認できる場合だけ設定する。
- 選択肢との一致を確認できない出席者は `出席者(テキスト)_` または `出席者` に保持する。
- `レビューア数` は出席者数と自動的に同一視せず、レビューアとして確認できる人数だけを設定する。
- `手動指摘件数` とAIが抽出したitems件数を混同しない。
- `判定` と `判定理由` は会議内または入力情報で明示された場合のみ設定する。

### Markdown表示原則

Markdownでは、以下を表示しない。

- `null`
- 空文字列
- `[]`
- 空オブジェクト

値のある項目だけを、Redmine上の項目名で列挙する。

```markdown
## Redmine登録情報

- ステータス: 完了
- 優先度: 通常
- 実施日: 2026-07-13
- 実施時間(開始): 10:00
- 実施時間(終了): 10:29
- DR/CR時間: 29分
- 出席者: I田、M田、H野
```


## アジェンダの扱い

アジェンダがある場合、各項目について以下を整理する。

- 何が決まったか
- 何が残ったか
- 誰が何をするか
- 次回までに何を確認するか

アジェンダ外の新規論点は `agenda_item_id: null` とする。


## 運営連絡の扱い

以下は通常、追跡対象にしない。

- 「不在があれば連絡ください」
- 「聞こえなければ言ってください」
- 「資料がなければ知らせてください」
- 「必要なら声をかけてください」

これらは `information` または抽出対象外とする。
ただし、特定の担当者、具体的対象、期限、完了条件が明示され、追跡合意がある場合は対応事項になり得る。


## 調査事項の判定

以下は `investigation` とする。

- 原因を調べる
- 再現条件を確認する
- 影響範囲を調査する
- ログや計測結果を確認する
- 仕様や外部条件を調べる

「修正する」と「調べる」は分ける。

例:

- `action_item`: 仕様書を修正する
- `investigation`: メモリ使用量が増加する条件を調査する
- `confirmation`: 顧客へ仕様意図を確認する

## 未決事項の判定

以下は `unresolved` とする。

- 問題提起だけで終わった
- 複数案から採用案を決められなかった
- 結論を次回へ持ち越した
- 時間切れで判断できなかった
- 関係者不在で決められなかった
- 指摘の妥当性について意見が割れた
- 対応は必要そうだが方法が未定

未決事項には以下を残す。

- 現時点の論点
- 合意済みの事実
- 未決内容
- 次の判断者
- 次回確認タイミング
- 必要な追加情報

## 決定・対応・調査を分ける例

- 決定事項: 通信失敗後は停止状態へ遷移する
- 対応事項: 佐藤が仕様書と状態遷移図を修正する
- 調査事項: 鈴木が再試行上限による影響を調査する

## JSON正本

出力は `meeting-open-items.schema.json` に適合させる。

```json
{
  "schema_version": "1.6",
  "meeting": {
    "title": "",
    "datetime": null,
    "project": null,
    "participants": [],
    "absent_people_mentioned": [],
    "mentioned_people": [],
    "agenda_source": null,
    "transcript_source": "",
    "extracted_at": ""
  },
  "agenda_items": [
    {
      "id": "AG-001",
      "title": "",
      "order": 1
    }
  ],
  "summary": {
    "decision_count": 0,
    "action_item_count": 0,
    "investigation_count": 0,
    "finding_count": 0,
    "unresolved_count": 0,
    "confirmation_count": 0,
    "hold_count": 0,
    "no_action_count": 0,
    "information_count": 0,
    "ticket_ready_count": 0,
    "needs_human_review_count": 0
  },
  "items": [
    {
      "id": "ITEM-001",
      "agenda_item_id": "AG-001",
      "title": "",
      "type": "action_item",
      "status": "open",
      "description": "",
      "rationale": null,
      "expected_state": null,
      "action_plan": null,
      "completion_criteria": [],
      "assignee": null,
      "assignee_speaker_id": null,
      "due_date": null,
      "next_review_timing": null,
      "discussion_summary": null,
      "superseded_conclusions": [],
      "possible_duplicate_of": null,
      "normalized_terms": [],
      "priority": null,
      "related_item_ids": [],
      "ticket_readiness": "conditionally_ready",
      "missing_information": [],
      "evidence": [
        {
          "timestamp": "",
          "speaker": "",
          "summary": ""
        }
      ],
      "redmine_issue_fields": {
        "ステータス": null,
        "優先度": null,
        "担当者": null,
        "対象バージョン": null,
        "開始日": null,
        "期日": null,
        "進捗率": null,
        "開発項目": null,
        "機能区分": null,
        "工程": null,
        "方式": null,
        "対象ドキュメント番号・表題": null,
        "_2_品質特性": null,
        "判定": null,
        "判定理由": null
      },
      "source_grounding": {
        "is_explicitly_stated": true,
        "support_level": "explicit"
      },
      "reviewer_comment": null
    }
  ],
  "human_review_required": []
}
```

## 列挙値

`status`:
- `open`
- `in_progress`
- `waiting_confirmation`
- `pending`
- `completed`
- `no_action`
- `agreed`
- `undetermined`

`ticket_readiness`:
- `ready`
- `conditionally_ready`
- `not_ready`

`priority`:
- `low`
- `medium`
- `high`
- `critical`
- `null`


## 議論内容の保持

`discussion` は原則として独立した残件種別にしない。

会議内で複数案を比較した経緯は、決定事項または未決事項の `discussion_summary` に残す。

例:

```json
{
  "type": "unresolved",
  "discussion_summary": "A案、B案、C案を比較したが、性能評価が不足しており採用案を決められなかった。"
}
```

議論だけが続き、追跡対象も結論も存在しない場合は、`type` を `information` とし、`ticket_readiness` は `not_ready` とする。



## missing_information の制限

`missing_information` は、成立済みの残件を実行または判定するために必要な不足だけを記録する。

記録してよい例:

- 調査担当者
- 対応期限
- 完了条件
- 次回判断者
- 対応要否

記録してはいけない例:

- 連絡チャネル
- 共有方法
- CC先
- 会議開催形式
- 会議で要求されていない親切情報



## 発言根拠レベル

各項目に `source_grounding` を持たせる。

- `explicit`: 会議内で明示された
- `strongly_implied`: 文脈上ほぼ確実だが明示されていない
- `ambiguous`: 複数解釈が可能
- `unsupported`: 発言根拠がない

追跡項目として採用できるのは原則 `explicit` のみ。
`strongly_implied` または `ambiguous` は人間確認へ回し、`unsupported` は削除する。


## チケット化判定

### ready
- タイトル
- 内容
- 対応方針
- 完了条件
- 担当者

が揃っている。

### conditionally_ready
残件としては明確だが、担当者、期限、完了条件などが不足している。

### not_ready
共有事項、雑談、対応不要、結論済み質問、内容不明。

## 処理手順

1. 会議情報とアジェンダを抽出する。
2. 文字起こしをアジェンダ項目へ対応付ける。
3. アジェンダ外の論点を抽出する。
4. 論点ごとの最終結論を確認する。
5. 追跡項目抽出ゲートを適用し、合意されていない候補を除外する。
6. 決定、対応、調査、指摘、未決、確認、保留などへ分類する。
7. 同一論点の再登場と結論反転を統合する。
8. 担当者、話者ID、期限、完了条件、次回確認時期を抽出する。
9. ASR誤認識候補を正規化候補として保持する。
10. 不足情報を必要最小限だけ `missing_information` に記録する。
11. 根拠発言を `evidence` に残す。
12. `source_grounding` を判定する。
13. チケット化可否を判定する。
14. `meeting_summary` を文字起こしと `items` に整合する形で生成する。
15. `redmine_meeting_fields` を全項目生成し、不明・非該当は `null` または `[]` とする。
16. 各itemに `redmine_issue_fields` を全項目生成し、`action_plan` を「処置内容」、`completion_criteria` を「確認内容」、確定日付を「確認日」へ割り当てる。
17. summaryを再集計する。
18. JSON Schemaで検証する。
19. `human_review_required` を作る。
20. JSONからMarkdownを生成し、Redmine項目は値のあるものだけ表示する。

## 未決事項の例

```json
{
  "id": "ITEM-003",
  "agenda_item_id": "AG-002",
  "title": "再試行上限の要否",
  "type": "unresolved",
  "status": "pending",
  "description": "再試行回数に上限がなく、永久再試行となる可能性がある。",
  "rationale": "懸念は共有されたが、対応要否と方式について合意できなかった。",
  "expected_state": null,
  "action_plan": "仕様担当が影響を確認し、次回会議で判断する。",
  "completion_criteria": [],
  "assignee": null,
  "assignee_speaker_id": null,
  "due_date": null,
  "next_review_timing": "次回定例会議",
  "discussion_summary": "上限なし継続案と回数制限案を比較したが、影響確認が不足していた。",
  "superseded_conclusions": [],
  "possible_duplicate_of": null,
  "normalized_terms": [],
  "priority": null,
  "related_item_ids": [],
  "ticket_readiness": "conditionally_ready",
  "missing_information": [
    "確認担当者",
    "対応要否",
    "完了条件",
    "次回会議日"
  ],
  "evidence": [
    {
      "timestamp": "00:31:10",
      "speaker": "山田",
      "summary": "再試行上限がない点を懸念として提示"
    },
    {
      "timestamp": "00:32:05",
      "speaker": "鈴木",
      "summary": "会議内では決めず次回へ持ち越すことで整理"
    }
  ],
  "reviewer_comment": null
}
```

## 出力品質チェック

- アジェンダと論点が対応付いている
- 同じ論点が重複していない
- 会話途中の意見を最終結論として扱っていない
- 指摘らしい未決事項を `finding` にしていない
- 決定事項、対応事項、調査事項を混同していない
- 質問を過剰に残件化していない
- 担当者や期限を推測していない
- 対応不要の理由を残している
- 未決事項に次の判断方法がある
- 同一論点の再登場を重複登録していない
- 結論反転時に最終結論を採用している
- 話者名不明時に実名を推測していない
- 欠席者や言及人物を参加者へ混入していない
- 発言にない確認事項やアクションを作っていない
- 意向表明を実施合意として扱っていない
- 運営連絡を過剰に残件化していない
- missing_informationを親切心で増やしていない
- 各追跡項目のsource_groundingがexplicitである
- ASR補正で原文を失っていない
- meeting_summaryが会議全体を俯瞰できる
- meeting_summaryがitemsと矛盾していない
- meeting_summaryから新しい対応事項を作っていない
- 次の進め方が明示されていない場合、next_step_summaryがnullである
- summary件数がitemsと一致する
- 子チケット内容欄の先頭に不要な「内容:」ラベルがない
- action_planが「処置内容」へ入り、内容欄へ重複していない
- completion_criteriaが「確認内容」へ入り、内容欄へ重複していない
- 絶対日付が確定できるnext_review_timingだけが「確認日」へ入る
- ITEM ID、type、ticket_readiness、source_groundingが通常の子チケット内容欄へ表示されていない
- JSONではredmine_meeting_fieldsとredmine_issue_fieldsの全項目が存在する
- 未取得・非該当のRedmine項目がnullまたは空配列である
- Markdownに空欄のRedmine項目を表示していない
- 「完了」を独立した項目名として出力していない
- 手動指摘件数とAI抽出件数を混同していない
- JSON Schemaに適合する

## 推奨運用

1. 会議前にアジェンダを用意する。
2. 会議終了後に文字起こしを取得する。
3. このSkillでJSONを生成する。
4. JSON Schemaで検証する。
5. JSONから会議全体の要旨を含むMarkdownを生成して回覧する。
6. 未決事項と不足情報だけ参加者が確認する。
7. 承認済みの対応事項・指摘事項・確認事項をチケット化する。
8. 次回会議で未決事項を再確認する。
