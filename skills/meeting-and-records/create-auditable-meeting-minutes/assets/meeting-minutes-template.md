# {{meeting.title}} 議事録

## 文書管理

- 文書番号: {{document_control.document_id}}
- 版: {{document_control.version}}
- 文書状態: {{document_control.approval_status}}
- 作成者: {{document_control.prepared_by}}
- レビュー者: {{document_control.reviewers}}
- 承認者: {{document_control.approvers}}
- 機密区分: {{document_control.confidentiality}}

値がない項目は一般版では省略し、正式版では「未確認」と表示する。

## 会議概要

- 日時: {{meeting.start_at}}–{{meeting.end_at}}
- 場所・接続方法: {{meeting.location}}
- 目的: {{meeting.purpose}}
- 出席者: {{meeting.participants}}
- 欠席者: {{meeting.absentees}}
- 使用資料: {{meeting.source_documents}}

## 全体要旨

{{meeting_summary}}

## 議題別記録

議題ごとに以下を繰り返す。

### {{agenda_item.number}}. {{agenda_item.title}}

- 背景: {{agenda_item.context}}
- 議論要旨: {{agenda_item.discussion_summary}}
- 主な発言・論拠: {{agenda_item.contributions}}
- 検討案: {{agenda_item.options_considered}}
- 異議・懸念・留保: {{agenda_item.dissent_and_reservations}}
- 結論: {{agenda_item.conclusion}}
- 最終状態: {{agenda_item.outcome}}
- 根拠: {{agenda_item.evidence}}

空の任意項目は省略する。

## 決定事項

{{decisions}}

## 対応事項

{{action_items}}

## 未決・保留事項

{{open_items}}

## 要確認事項

{{review_flags}}

正式版では空でも「なし」または「未確認」を明示する。

## 改訂履歴

{{revision_history}}
