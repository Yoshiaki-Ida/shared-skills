from pathlib import Path
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]
POWERSHELL = shutil.which('powershell.exe') or shutil.which('pwsh')
pytestmark = pytest.mark.skipif(not POWERSHELL, reason='PowerShell is required')


def run_install(home, *options):
    return subprocess.run(
        [POWERSHELL, '-NoProfile', '-File', str(ROOT / 'scripts/install.ps1'),
         '-UserHome', str(home), *options],
        capture_output=True, timeout=60,
    )


def test_preview_does_not_create_personal_directories(tmp_path):
    result = run_install(tmp_path)
    assert result.returncode == 0, result.stderr
    assert b'PREVIEW' in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_install_conflict_and_update_preserve_personal_files(tmp_path):
    result = run_install(tmp_path, '-Apply')
    assert result.returncode == 0, result.stderr
    assert b'INSTALL_PASS' in result.stdout
    target = tmp_path / '.agents/skills/create-auditable-meeting-minutes/SKILL.md'
    source = ROOT / 'skills/meeting-and-records/create-auditable-meeting-minutes/SKILL.md'
    assert target.read_bytes() == source.read_bytes()
    assert (tmp_path / '.copilot/agents/redmine-meeting-orchestrator.agent.md').is_file()
    personal = target.parent / 'personal-notes.txt'
    personal.write_text('Keep this file', encoding='utf-8')
    target.write_text('Personal customization', encoding='utf-8')
    result = run_install(tmp_path, '-Apply')
    assert result.returncode != 0
    assert target.read_text(encoding='utf-8') == 'Personal customization'
    result = run_install(tmp_path, '-Apply', '-Update')
    assert result.returncode == 0, result.stderr
    assert target.read_bytes() == source.read_bytes()
    assert personal.read_text(encoding='utf-8') == 'Keep this file'
    result = run_install(tmp_path)
    assert b'CONFLICT' not in result.stdout
    assert b'NEW' not in result.stdout