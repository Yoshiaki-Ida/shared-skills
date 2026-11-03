#!/usr/bin/env python3
"""Render auditable minutes JSON into Redmine import JSON and human-readable HTML."""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REDMINE_SCHEMA_VERSION = "1.6"
REDMINE_PARENT_FIELDS = (
    "ステータス", "優先度", "担当者", "対象バージョン", "開始日", "期日", "進捗率",
    "開発項目", "機能区分", "開催回数", "議事録番号", "工程", "方式",
    "対象ドキュメント番号・表題", "実施日", "実施時間(開始)", "実施時間(終了)",
    "DR/CR時間", "実施場所", "出席者_選択_", "出席者_テキスト_", "レビューア人数",
    "DR対象頁数・ライン数(L)・項目数", "全体頁数・ライン数(L)・項目数",
    "手動指摘件数", "手動", "DRチェッカー", "_2_品質特性", "判定", "判定理由", "出席者",
)
REDMINE_CHILD_FIELDS = (
    "ステータス", "優先度", "担当者", "対象バージョン", "開始日", "期日", "進捗率",
    "開発項目", "機能区分", "工程", "方式", "対象ドキュメント番号・表題",
    "処置内容", "確認内容", "確認日", "指摘日", "_2_品質特性", "判定", "判定理由",
)
OUTCOME_LABELS = {
    "decided": "決定",
    "approved": "承認",
    "conditionally_approved": "条件付き承認",
    "rejected": "否決",
    "deferred": "保留",
    "unresolved": "未決",
    "information_only": "情報共有",
}
APPROVAL_LABELS = {
    "draft": "ドラフト",
    "under_review": "レビュー中",
    "approved": "承認済み",
    "rejected": "差戻し",
    "superseded": "旧版",
    "unknown": "未確認",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Redmine meeting-open-items JSON, HTML minutes, and a validation report."
    )
    parser.add_argument("source_json", type=Path, help="Canonical meeting-minutes JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for generated files")
    parser.add_argument(
        "--redmine-filename", default="redmine-import.json", help="Redmine JSON output filename"
    )
    parser.add_argument("--html-filename", default="meeting-minutes.html", help="HTML output filename")
    parser.add_argument(
        "--report-filename", default="validation-report.json", help="Validation report filename"
    )
    return parser.parse_args()


def load_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Top-level JSON must be an object")
    return data


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def iso_date(value: Any) -> str | None:
    raw = text(value)
    if not raw:
        return None
    return raw[:10] if len(raw) >= 10 and raw[4:5] == "-" and raw[7:8] == "-" else None


def iso_time(value: Any) -> str | None:
    raw = text(value)
    if "T" not in raw:
        return None
    portion = raw.split("T", 1)[1]
    return portion[:5] if len(portion) >= 5 else None


def evidence_rows(rows: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in as_list(rows):
        item = as_dict(row)
        result.append(
            {
                "timestamp": item.get("timestamp"),
                "speaker": item.get("speaker"),
                "summary": text(item.get("summary")),
            }
        )
    return result


def agenda_index(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        text(row.get("id")): row
        for raw in as_list(source.get("agenda_items"))
        if (row := as_dict(raw)) and text(row.get("id"))
    }


def make_title(statement: str, fallback: str) -> str:
    normalized = " ".join(statement.split())
    if not normalized:
        return fallback
    return normalized if len(normalized) <= 60 else normalized[:59] + "…"


def ticket_readiness(owner: Any, criteria: Any, due_date: Any) -> tuple[str, list[str]]:
    missing: list[str] = []
    if not text(owner):
        missing.append("担当者")
    if not text(criteria):
        missing.append("完了条件")
    if not text(due_date):
        missing.append("期限")
    return ("ready" if not missing else "conditionally_ready", missing)


def base_child_fields() -> dict[str, Any]:
    return {key: None for key in REDMINE_CHILD_FIELDS}


def action_to_item(action: dict[str, Any], agendas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    action_text = text(action.get("action"))
    agenda = agendas.get(text(action.get("agenda_item_id")), {})
    criteria = text(action.get("completion_criteria"))
    readiness, missing = ticket_readiness(action.get("owner"), criteria, action.get("due_date"))
    fields = base_child_fields()
    fields.update(
        {
            "担当者": action.get("owner"),
            "期日": iso_date(action.get("due_date")),
            "処置内容": action_text or None,
            "確認内容": criteria or None,
        }
    )
    return {
        "id": text(action.get("id")),
        "agenda_item_id": action.get("agenda_item_id"),
        "title": make_title(action_text, "対応事項"),
        "type": "action_item",
        "status": text(action.get("status")) or "open",
        "description": action_text,
        "rationale": agenda.get("context"),
        "expected_state": criteria or None,
        "action_plan": action_text or None,
        "completion_criteria": [criteria] if criteria else [],
        "assignee": action.get("owner"),
        "assignee_speaker_id": None,
        "due_date": iso_date(action.get("due_date")),
        "next_review_timing": None,
        "discussion_summary": agenda.get("discussion_summary"),
        "superseded_conclusions": [],
        "possible_duplicate_of": None,
        "normalized_terms": [],
        "priority": None,
        "related_item_ids": [],
        "ticket_readiness": readiness,
        "missing_information": missing,
        "evidence": evidence_rows(action.get("evidence")),
        "redmine_issue_fields": fields,
        "source_grounding": {"is_explicitly_stated": True, "support_level": "explicit"},
        "reviewer_comment": None,
    }


def open_to_item(open_item: dict[str, Any], agendas: dict[str, dict[str, Any]]) -> dict[str, Any]:
    statement = text(open_item.get("statement"))
    agenda = agendas.get(text(open_item.get("agenda_item_id")), {})
    next_method = text(open_item.get("next_decision_method"))
    missing = []
    if not text(open_item.get("owner")):
        missing.append("次の判断担当者")
    if not next_method:
        missing.append("次の判断方法")
    fields = base_child_fields()
    fields.update(
        {
            "担当者": open_item.get("owner"),
            "期日": iso_date(open_item.get("target_date")),
            "処置内容": next_method or None,
            "確認内容": None,
        }
    )
    return {
        "id": text(open_item.get("id")),
        "agenda_item_id": open_item.get("agenda_item_id"),
        "title": make_title(statement, "未決事項"),
        "type": "unresolved",
        "status": "pending",
        "description": statement,
        "rationale": open_item.get("reason_open") or agenda.get("context"),
        "expected_state": None,
        "action_plan": next_method or None,
        "completion_criteria": [],
        "assignee": open_item.get("owner"),
        "assignee_speaker_id": None,
        "due_date": iso_date(open_item.get("target_date")),
        "next_review_timing": open_item.get("target_date"),
        "discussion_summary": agenda.get("discussion_summary"),
        "superseded_conclusions": as_list(agenda.get("decision_history")),
        "possible_duplicate_of": None,
        "normalized_terms": [],
        "priority": None,
        "related_item_ids": [],
        "ticket_readiness": "conditionally_ready" if statement else "not_ready",
        "missing_information": missing,
        "evidence": evidence_rows(agenda.get("evidence")),
        "redmine_issue_fields": fields,
        "source_grounding": {"is_explicitly_stated": True, "support_level": "explicit"},
        "reviewer_comment": None,
    }


def convert_to_redmine(source: dict[str, Any]) -> dict[str, Any]:
    meeting = as_dict(source.get("meeting"))
    control = as_dict(source.get("document_control"))
    agendas = agenda_index(source)
    actions = [as_dict(x) for x in as_list(source.get("action_items"))]
    opens = [as_dict(x) for x in as_list(source.get("open_items"))]
    decisions = [as_dict(x) for x in as_list(source.get("decisions"))]
    items = [action_to_item(x, agendas) for x in actions] + [open_to_item(x, agendas) for x in opens]

    redmine_meeting_fields = {key: None for key in REDMINE_PARENT_FIELDS}
    participants = [
        text(p.get("name")) or text(p.get("speaker_id"))
        for raw in as_list(meeting.get("participants"))
        if (p := as_dict(raw)) and (text(p.get("name")) or text(p.get("speaker_id")))
    ]
    documents = [
        " ".join(x for x in [text(d.get("title")), text(d.get("version"))] if x)
        for raw in as_list(meeting.get("source_documents"))
        if (d := as_dict(raw)) and text(d.get("title"))
    ]
    redmine_meeting_fields.update(
        {
            "議事録番号": control.get("document_id"),
            "対象ドキュメント番号・表題": "\n".join(documents) or None,
            "実施日": iso_date(meeting.get("start_at")),
            "実施時間(開始)": iso_time(meeting.get("start_at")),
            "実施時間(終了)": iso_time(meeting.get("end_at")),
            "実施場所": meeting.get("location"),
            "出席者_テキスト_": "、".join(participants) or None,
            "出席者": "、".join(participants) or None,
            "判定": APPROVAL_LABELS.get(text(control.get("approval_status"))) or None,
        }
    )
    key_outcomes = [text(x.get("statement")) for x in decisions if text(x.get("statement"))]
    key_outcomes += [text(x.get("action")) for x in actions if text(x.get("action"))]
    open_points = [text(x.get("statement")) for x in opens if text(x.get("statement"))]
    main_topics = [text(x.get("title")) for x in agendas.values() if text(x.get("title"))]
    next_steps = [text(x.get("next_decision_method")) for x in opens if text(x.get("next_decision_method"))]
    next_steps += [text(x.get("action")) for x in actions if text(x.get("action"))]
    flags = [as_dict(x) for x in as_list(source.get("review_flags"))]

    ready_count = sum(1 for x in items if x["ticket_readiness"] == "ready")
    return {
        "schema_version": REDMINE_SCHEMA_VERSION,
        "meeting": {
            "title": text(meeting.get("title")),
            "datetime": meeting.get("start_at"),
            "project": None,
            "participants": participants,
            "absent_people_mentioned": [
                text(p.get("name")) or text(p.get("speaker_id"))
                for raw in as_list(meeting.get("absentees"))
                if (p := as_dict(raw)) and (text(p.get("name")) or text(p.get("speaker_id")))
            ],
            "mentioned_people": [],
            "agenda_source": None,
            "transcript_source": "",
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        },
        "redmine_meeting_fields": redmine_meeting_fields,
        "agenda_items": [
            {"id": text(x.get("id")), "title": text(x.get("title")), "order": x.get("number")}
            for x in agendas.values()
        ],
        "meeting_summary": {
            "overview": text(source.get("meeting_summary")),
            "main_topics": main_topics,
            "key_outcomes": key_outcomes,
            "open_points": open_points,
            "next_step_summary": " / ".join(dict.fromkeys(next_steps)) or None,
        },
        "summary": {
            "decision_count": len(decisions),
            "action_item_count": len(actions),
            "investigation_count": 0,
            "finding_count": 0,
            "unresolved_count": len(opens),
            "confirmation_count": 0,
            "hold_count": 0,
            "no_action_count": 0,
            "information_count": 0,
            "ticket_ready_count": ready_count,
            "needs_human_review_count": len(flags),
        },
        "items": items,
        "human_review_required": [
            {
                "id": text(flag.get("id")),
                "reason": text(flag.get("issue")),
                "severity": text(flag.get("severity")),
                "required_resolution": flag.get("required_resolution"),
            }
            for flag in flags
        ],
    }


def h(value: Any) -> str:
    return html.escape(text(value), quote=True)


def list_html(values: Any, empty: str = "なし") -> str:
    rows = [text(x) for x in as_list(values) if text(x)]
    if not rows:
        return f'<p class="empty">{h(empty)}</p>'
    return "<ul>" + "".join(f"<li>{h(row)}</li>" for row in rows) + "</ul>"


def evidence_html(rows: Any) -> str:
    rendered: list[str] = []
    for raw in as_list(rows):
        row = as_dict(raw)
        meta = " / ".join(
            x
            for x in [
                text(row.get("timestamp")),
                text(row.get("speaker")),
                text(row.get("document")),
                text(row.get("locator")),
            ]
            if x
        )
        rendered.append(f"<li><span>{h(meta)}</span>{h(row.get('summary'))}</li>")
    return "<ul class=\"evidence\">" + "".join(rendered) + "</ul>" if rendered else '<p class="empty">なし</p>'


def people_text(rows: Any) -> str:
    values: list[str] = []
    for raw in as_list(rows):
        row = as_dict(raw)
        name = text(row.get("name")) or text(row.get("speaker_id")) or "未確認"
        role = text(row.get("role"))
        values.append(f"{name}（{role}）" if role else name)
    return "、".join(values) or "なし"


def render_html(source: dict[str, Any]) -> str:
    meeting = as_dict(source.get("meeting"))
    control = as_dict(source.get("document_control"))
    agendas = [as_dict(x) for x in as_list(source.get("agenda_items"))]
    decisions = [as_dict(x) for x in as_list(source.get("decisions"))]
    actions = [as_dict(x) for x in as_list(source.get("action_items"))]
    opens = [as_dict(x) for x in as_list(source.get("open_items"))]
    flags = [as_dict(x) for x in as_list(source.get("review_flags"))]
    blocking = any(text(x.get("severity")) == "blocking" for x in flags)
    status = APPROVAL_LABELS.get(text(control.get("approval_status")), "未確認")
    status_class = "danger" if blocking else ("approved" if control.get("approval_status") == "approved" else "draft")

    agenda_sections: list[str] = []
    for agenda in agendas:
        contributions = []
        for raw in as_list(agenda.get("contributions")):
            row = as_dict(raw)
            speaker = text(row.get("speaker")) or text(row.get("speaker_id")) or "話者不明"
            contributions.append(
                f"<li><strong>{h(speaker)}</strong><p>{h(row.get('summary'))}</p>"
                f"<p class=\"position\">立場・論点: {h(row.get('position') or '未確認')}</p>"
                f"{evidence_html(row.get('evidence'))}</li>"
            )
        agenda_sections.append(
            f"""<article class="agenda">
<h3>{h(agenda.get('number'))}. {h(agenda.get('title'))}</h3>
<dl>
<dt>背景</dt><dd>{h(agenda.get('context') or '未確認')}</dd>
<dt>議論要旨</dt><dd>{h(agenda.get('discussion_summary'))}</dd>
<dt>最終状態</dt><dd><span class="badge">{h(OUTCOME_LABELS.get(text(agenda.get('outcome')), agenda.get('outcome')))}</span></dd>
<dt>結論</dt><dd>{h(agenda.get('conclusion') or '未決')}</dd>
</dl>
<h4>主な発言・論拠</h4><ul class="contributions">{''.join(contributions) or '<li class="empty">なし</li>'}</ul>
<h4>検討案</h4>{list_html(agenda.get('options_considered'))}
<h4>異議・懸念・留保</h4>{list_html(agenda.get('dissent_and_reservations'))}
<h4>結論の変遷</h4>{list_html(agenda.get('decision_history'))}
<details><summary>根拠</summary>{evidence_html(agenda.get('evidence'))}</details>
</article>"""
        )

    decision_rows = "".join(
        f"<tr><td>{h(x.get('id'))}</td><td>{h(x.get('statement'))}</td><td>{h(x.get('rationale') or '')}</td>"
        f"<td>{h('、'.join(text(y) for y in as_list(x.get('decided_by')) if text(y)))}</td></tr>"
        for x in decisions
    )
    action_rows = "".join(
        f"<tr><td>{h(x.get('id'))}</td><td>{h(x.get('action'))}</td><td>{h(x.get('owner') or '未定')}</td>"
        f"<td>{h(x.get('due_date') or '未定')}</td><td>{h(x.get('completion_criteria') or '未確認')}</td></tr>"
        for x in actions
    )
    open_rows = "".join(
        f"<tr><td>{h(x.get('id'))}</td><td>{h(x.get('statement'))}</td><td>{h(x.get('reason_open') or '')}</td>"
        f"<td>{h(x.get('next_decision_method') or '未確認')}</td></tr>"
        for x in opens
    )
    flag_rows = "".join(
        f"<li class=\"flag {h(x.get('severity'))}\"><strong>{h(x.get('subject'))}</strong>: "
        f"{h(x.get('issue'))}<br><span>解消方法: {h(x.get('required_resolution') or '未確認')}</span></li>"
        for x in flags
    )
    revisions = "".join(
        f"<tr><td>{h(x.get('version'))}</td><td>{h(x.get('changed_at') or '')}</td>"
        f"<td>{h(x.get('changed_by') or '')}</td><td>{h(x.get('reason'))}</td>"
        f"<td>{h(' / '.join(text(y) for y in as_list(x.get('changes')) if text(y)))}</td></tr>"
        for x in (as_dict(r) for r in as_list(source.get("revision_history")))
    )
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{h(meeting.get('title'))} 議事録</title>
<style>
:root{{--ink:#182230;--muted:#5f6b7a;--line:#d8dee7;--paper:#fff;--accent:#155eef;--soft:#eef4ff;--warn:#b54708;--danger:#b42318}}
*{{box-sizing:border-box}}body{{margin:0;background:#f4f6f8;color:var(--ink);font-family:"Yu Gothic UI","Noto Sans JP",sans-serif;line-height:1.7}}
main{{max-width:1120px;margin:32px auto;padding:40px 52px;background:var(--paper);box-shadow:0 8px 30px #172b4d1a}}
h1,h2,h3{{line-height:1.35}}h1{{margin:0 0 8px;font-size:2rem}}h2{{margin-top:42px;border-bottom:2px solid var(--ink);padding-bottom:8px}}h3{{margin-top:0}}h4{{margin-bottom:6px}}
.doc-meta,.meeting-meta{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px 20px;padding:18px;background:#f8fafc;border:1px solid var(--line)}}
.doc-meta dt,.meeting-meta dt,dl dt{{color:var(--muted);font-size:.85rem;font-weight:700}}.doc-meta dd,.meeting-meta dd,dl dd{{margin:0}}
.status{{display:inline-block;padding:4px 10px;border-radius:999px;background:#f2f4f7}}.status.approved{{background:#dcfae6;color:#067647}}.status.danger{{background:#fee4e2;color:var(--danger)}}
.agenda{{margin:20px 0;padding:24px;border:1px solid var(--line);border-left:5px solid var(--accent)}}.agenda dl{{display:grid;grid-template-columns:110px 1fr;gap:8px 16px}}
.badge{{background:var(--soft);color:#1849a9;padding:3px 8px;border-radius:4px}}.empty{{color:var(--muted)}}.position{{color:var(--muted);margin:.2rem 0}}
.contributions>li{{margin-bottom:16px}}.evidence{{font-size:.9rem;color:var(--muted)}}.evidence span{{font-weight:700;margin-right:8px}}
table{{width:100%;border-collapse:collapse;font-size:.94rem}}th,td{{border:1px solid var(--line);padding:9px;vertical-align:top}}th{{background:#f2f4f7;text-align:left}}
.flags{{padding:0;list-style:none}}.flag{{padding:12px;margin:8px 0;background:#fff7ed;border-left:4px solid var(--warn)}}.flag.blocking{{background:#fef3f2;border-color:var(--danger)}}
footer{{margin-top:44px;padding-top:12px;border-top:1px solid var(--line);color:var(--muted);font-size:.85rem}}
@media(max-width:760px){{main{{margin:0;padding:24px 18px}}.doc-meta,.meeting-meta{{grid-template-columns:1fr}}.agenda dl{{grid-template-columns:1fr}}table{{display:block;overflow:auto}}}}
@media print{{body{{background:#fff}}main{{max-width:none;margin:0;padding:0;box-shadow:none}}.agenda{{break-inside:avoid}}details{{display:block}}}}
</style></head><body><main>
<header><p>MEETING MINUTES</p><h1>{h(meeting.get('title'))}</h1><span class="status {status_class}">{h(status)}</span></header>
<section><h2>文書管理</h2><dl class="doc-meta">
<div><dt>文書番号</dt><dd>{h(control.get('document_id') or '未確認')}</dd></div>
<div><dt>版</dt><dd>{h(control.get('version') or '未確認')}</dd></div>
<div><dt>作成者</dt><dd>{h(control.get('prepared_by') or '未確認')}</dd></div>
<div><dt>レビュー者</dt><dd>{h('、'.join(text(x) for x in as_list(control.get('reviewers')) if text(x)) or '未確認')}</dd></div>
<div><dt>承認者</dt><dd>{h('、'.join(text(x) for x in as_list(control.get('approvers')) if text(x)) or '未確認')}</dd></div>
<div><dt>機密区分</dt><dd>{h(control.get('confidentiality') or '未確認')}</dd></div></dl></section>
<section><h2>会議概要</h2><dl class="meeting-meta">
<div><dt>開始</dt><dd>{h(meeting.get('start_at') or '未確認')}</dd></div><div><dt>終了</dt><dd>{h(meeting.get('end_at') or '未確認')}</dd></div>
<div><dt>場所</dt><dd>{h(meeting.get('location') or '未確認')}</dd></div><div><dt>目的</dt><dd>{h(meeting.get('purpose') or '未確認')}</dd></div>
<div><dt>出席者</dt><dd>{h(people_text(meeting.get('participants')))}</dd></div><div><dt>欠席者</dt><dd>{h(people_text(meeting.get('absentees')))}</dd></div>
</dl></section>
<section><h2>全体要旨</h2><p>{h(source.get('meeting_summary'))}</p></section>
<section><h2>議題別記録</h2>{''.join(agenda_sections) or '<p class="empty">議題なし</p>'}</section>
<section><h2>決定事項</h2><table><thead><tr><th>ID</th><th>決定</th><th>理由</th><th>決定者</th></tr></thead><tbody>{decision_rows or '<tr><td colspan="4">なし</td></tr>'}</tbody></table></section>
<section><h2>対応事項</h2><table><thead><tr><th>ID</th><th>対応</th><th>担当</th><th>期限</th><th>完了条件</th></tr></thead><tbody>{action_rows or '<tr><td colspan="5">なし</td></tr>'}</tbody></table></section>
<section><h2>未決・保留事項</h2><table><thead><tr><th>ID</th><th>事項</th><th>理由</th><th>次の判断方法</th></tr></thead><tbody>{open_rows or '<tr><td colspan="4">なし</td></tr>'}</tbody></table></section>
<section><h2>要確認事項</h2><ul class="flags">{flag_rows or '<li class="empty">なし</li>'}</ul></section>
<section><h2>改訂履歴</h2><table><thead><tr><th>版</th><th>日時</th><th>変更者</th><th>理由</th><th>変更内容</th></tr></thead><tbody>{revisions or '<tr><td colspan="5">なし</td></tr>'}</tbody></table></section>
<footer>このHTMLは正本JSONから自動生成されています。内容を修正する場合は正本JSONを更新して再生成してください。</footer>
</main></body></html>"""


def validate_source(source: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = (
        "schema_version", "mode", "meeting", "document_control", "meeting_summary",
        "agenda_items", "decisions", "action_items", "open_items", "review_flags", "revision_history",
    )
    for key in required:
        if key not in source:
            errors.append(f"missing_top_level:{key}")
    ids: list[str] = []
    for key in ("agenda_items", "decisions", "action_items", "open_items", "review_flags"):
        for raw in as_list(source.get(key)):
            row = as_dict(raw)
            item_id = text(row.get("id"))
            if not item_id:
                errors.append(f"missing_id:{key}")
            else:
                ids.append(item_id)
    for duplicate, count in Counter(ids).items():
        if count > 1:
            errors.append(f"duplicate_id:{duplicate}")
    if source.get("mode") == "formal":
        control = as_dict(source.get("document_control"))
        for key in ("document_id", "version", "prepared_by"):
            if not text(control.get(key)):
                warnings.append(f"formal_document_control_missing:{key}")
    blocking = [
        text(as_dict(x).get("id"))
        for x in as_list(source.get("review_flags"))
        if text(as_dict(x).get("severity")) == "blocking"
    ]
    if blocking and as_dict(source.get("document_control")).get("approval_status") == "approved":
        errors.append("approved_document_has_blocking_review_flags")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "blocking_review_flag_ids": blocking,
    }


def main() -> int:
    args = parse_args()
    try:
        source = load_object(args.source_json)
        report = validate_source(source)
        if not report["valid"]:
            print(json.dumps(report, ensure_ascii=False, indent=2), file=sys.stderr)
            return 2
        redmine = convert_to_redmine(source)
        rendered_html = render_html(source)
        report.update(
            {
                "source_schema_version": source.get("schema_version"),
                "redmine_schema_version": REDMINE_SCHEMA_VERSION,
                "counts": {
                    "agenda_items": len(as_list(source.get("agenda_items"))),
                    "decisions": len(as_list(source.get("decisions"))),
                    "action_items": len(as_list(source.get("action_items"))),
                    "open_items": len(as_list(source.get("open_items"))),
                    "redmine_child_items": len(as_list(redmine.get("items"))),
                },
                "redmine_excluded": {
                    "decisions": len(as_list(source.get("decisions"))),
                    "reason": "決定事項は親議事録へ記載し、作業または未決事項のみ子チケット化する。",
                },
            }
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / args.redmine_filename).write_text(
            json.dumps(redmine, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (args.output_dir / args.html_filename).write_text(rendered_html, encoding="utf-8")
        (args.output_dir / args.report_filename).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
