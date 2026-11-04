from pathlib import Path
import json
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


def test_all_six_skills_and_nested_references_are_installed(tmp_path):
    result = run_install(tmp_path, '-Apply')
    assert result.returncode == 0, result.stderr
    assert b'6 Skills and one Agent' in result.stdout
    definitions = list((ROOT / 'skills').glob('*/*/SKILL.md'))
    assert len(definitions) == 6
    for definition in definitions:
        source = definition.parent
        destination = tmp_path / '.agents/skills' / source.name
        for path in source.rglob('*'):
            if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
                assert (destination / path.relative_to(source)).read_bytes() == path.read_bytes()
    result = run_install(tmp_path)
    assert result.returncode == 0, result.stderr
    assert b'CONFLICT' not in result.stdout
    assert b'NEW' not in result.stdout


@pytest.mark.parametrize('newline', [b'\n', b'\r\n'])
def test_line_endings_do_not_conflict_or_overwrite(tmp_path, newline):
    result = run_install(tmp_path, '-Apply')
    assert result.returncode == 0, result.stderr
    contents = {}
    for target in tmp_path.rglob('*'):
        if target.is_file():
            content = target.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', newline)
            target.write_bytes(content)
            contents[target] = content
    result = run_install(tmp_path, '-Apply')
    assert result.returncode == 0, result.stderr
    assert b'CONFLICT' not in result.stdout
    assert b'INSTALL_PASS' in result.stdout
    for target, content in contents.items():
        assert target.read_bytes() == content
    assert not (tmp_path / '.agents/backups').exists()


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
    assert b'BACKUP:' in result.stdout
    manifests = list((tmp_path / '.agents/backups/shared-skills').glob('*/manifest.json'))
    assert len(manifests) == 1
    entries = json.loads(manifests[0].read_text(encoding='utf-8-sig'))
    assert len(entries) == 1
    assert Path(entries[0]['Target']) == target
    assert Path(entries[0]['Backup']).read_text(encoding='utf-8') == 'Personal customization'
    assert target.read_bytes() == source.read_bytes()
    assert personal.read_text(encoding='utf-8') == 'Keep this file'
    result = run_install(tmp_path)
    assert b'CONFLICT' not in result.stdout
    assert b'NEW' not in result.stdout


def test_backup_failure_leaves_installation_unchanged(tmp_path):
    result = run_install(tmp_path, '-Apply')
    assert result.returncode == 0, result.stderr
    target = tmp_path / '.agents/skills/create-auditable-meeting-minutes/SKILL.md'
    target.write_text('Personal customization', encoding='utf-8')
    installed = {path: path.read_bytes() for path in tmp_path.rglob('*') if path.is_file()}
    (tmp_path / '.agents/backups').write_text('Block backup directory', encoding='utf-8')
    result = run_install(tmp_path, '-Apply', '-Update')
    assert result.returncode != 0
    assert b'INSTALL_PASS' not in result.stdout
    for path, content in installed.items():
        assert path.read_bytes() == content


@pytest.mark.parametrize('change', ['case', 'space', 'encoding'])
def test_content_differences_still_stop_without_update(tmp_path, change):
    result = run_install(tmp_path, '-Apply')
    assert result.returncode == 0, result.stderr
    target = tmp_path / '.agents/skills/create-auditable-meeting-minutes/SKILL.md'
    content = target.read_bytes()
    if change == 'case':
        content = content.replace(b'name:', b'Name:', 1)
    elif change == 'space':
        content += b' '
    else:
        content += b'\xff'
    target.write_bytes(content)
    result = run_install(tmp_path, '-Apply')
    assert result.returncode != 0
    assert b'CONFLICT' in result.stdout
    assert target.read_bytes() == content
    assert not (tmp_path / '.agents/backups').exists()