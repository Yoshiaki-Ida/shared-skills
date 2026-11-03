import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
APP = Path(os.environ.get('ITEMS_APP_ROOT', ROOT.parent / 'Items/redmine-ticket-correction'))


@pytest.mark.skipif(not APP.is_dir(), reason='Place Items beside shared-skills, or set ITEMS_APP_ROOT')
def test_minutes_to_dry_run_apply_and_export(tmp_path, monkeypatch):
    skill = ROOT / 'skills/meeting-and-records/create-auditable-meeting-minutes'
    result = subprocess.run(
        [sys.executable, '-B', str(skill / 'scripts/render_minutes_outputs.py'),
         str(skill / 'assets/example-minutes-source.json'), '--output-dir', str(tmp_path)],
        capture_output=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / 'validation-report.json').read_text(encoding='utf-8'))['valid']
    assert (tmp_path / 'meeting-minutes.html').stat().st_size > 100

    monkeypatch.syspath_prepend(str(APP / 'src'))
    from ticket_tools.ticket_creation import redmine_meeting_importer as importer
    from ticket_tools.ticket_creation import redmine_to_markdown as exporter

    assert Path(importer.__file__).resolve().is_relative_to(APP.resolve())
    monkeypatch.setattr(importer, '_get_windows_user_environment_variable', lambda name: 'test-only-key')
    monkeypatch.setenv('REDMINE_API_KEY', 'test-only-key')
    issues = []
    calls = []

    class FakeClient(importer.RedmineClient):
        def request_json(self, method, path, payload=None):
            calls.append(method)
            path = path.lstrip('/')
            if method == 'POST':
                issue = dict(payload['issue'], id=len(issues) + 1)
                issues.append(issue)
                return {'issue': issue}
            if path == 'issues.json':
                matches = issues
                if payload and payload.get('subject'):
                    matches = [issue for issue in issues if issue['subject'] == payload['subject']]
                return {'issues': matches, 'total_count': len(matches)}
            issue_id = int(path.split('/')[1].split('.')[0])
            return {'issue': next(issue for issue in issues if issue['id'] == issue_id)}

    monkeypatch.setattr(importer, 'RedmineClient', FakeClient)
    monkeypatch.setattr(exporter, 'ApiClient', FakeClient)
    arguments = [str(tmp_path / 'redmine-import.json'), '--config',
                 str(APP / 'config/config.example.json'), '--project-id', 'demo',
                 '--parent-tracker-id', '6', '--child-tracker-id', '20']
    assert importer.run(arguments + ['--output', str(tmp_path / 'preview.json')]) == 0
    assert calls == []
    preview = json.loads((tmp_path / 'preview.json').read_text(encoding='utf-8'))
    assert preview['mode'] == 'dry-run'
    assert len(preview['children']) == 2
    assert importer.run(arguments + ['--apply', '--confirm-create-parent',
                                    '--output', str(tmp_path / 'apply.json')]) == 0
    applied = json.loads((tmp_path / 'apply.json').read_text(encoding='utf-8'))
    assert applied['failed_items'] == []
    assert len(issues) == 3
    assert all(issue['parent_issue_id'] == 1 for issue in issues[1:])
    output = tmp_path / 'export/tickets.md'
    monkeypatch.setattr(sys, 'argv', ['export', '--project', 'demo', '--config',
                                    str(APP / 'config/config.example.json'), '--output', str(output)])
    assert exporter.main() == 0
    markdown = output.read_text(encoding='utf-8')
    for issue in issues:
        assert issue['subject'] in markdown
        assert f"/issues/{issue['id']}" in markdown