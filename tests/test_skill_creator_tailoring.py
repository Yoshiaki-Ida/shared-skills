import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/skill-management/skill-creator'


class SkillCreatorTailoringTests(unittest.TestCase):
    def test_upstream_snapshot_matches_provenance(self):
        provenance = json.loads((SKILL / 'references/upstream-provenance.json').read_text(encoding='utf-8'))
        self.assertEqual(len(provenance['files']), 18)
        for item in provenance['files']:
            with self.subTest(source=item['source']):
                target = (SKILL / item['target']).resolve()
                self.assertTrue(target.is_relative_to(SKILL.resolve()))
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), item['sha256'])
        definitions = [p.relative_to(SKILL).as_posix() for p in SKILL.rglob('SKILL.md')]
        self.assertEqual(definitions, ['SKILL.md'])

    def test_entry_links_and_original_runtime_paths_exist(self):
        entry = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', entry):
            self.assertTrue((SKILL / target).is_file(), target)
        for relative in ['agents/grader.md', 'agents/comparator.md', 'agents/analyzer.md',
                         'references/schemas.md', 'scripts/aggregate_benchmark.py',
                         'scripts/run_loop.py', 'eval-viewer/generate_review.py']:
            self.assertTrue((SKILL / relative).is_file(), relative)

    def test_local_validator_preserves_japanese_and_name_checks(self):
        spec = importlib.util.spec_from_file_location('tailored_skill_validator', SKILL / 'scripts/quick_validate.py')
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        with tempfile.TemporaryDirectory() as directory:
            skill = Path(directory) / 'sample'
            skill.mkdir()
            definition = skill / 'SKILL.md'
            definition.write_text('---\nname: sample\ndescription: 日本語の文書を整理する\ncompatibility: Codex / Copilot\n---\n本文\n', encoding='utf-8')
            self.assertTrue(validator.validate_skill(skill)[0])
            definition.write_text('---\nname: wrong-name\ndescription: 日本語\n---\n', encoding='utf-8')
            self.assertFalse(validator.validate_skill(skill)[0])

    def test_offline_tools_start(self):
        commands = [
            ['-m', 'scripts.aggregate_benchmark', '--help'],
            ['eval-viewer/generate_review.py', '--help'],
        ]
        for arguments in commands:
            with self.subTest(command=arguments):
                result = subprocess.run([sys.executable, '-X', 'utf8', '-B', *arguments],
                                        cwd=SKILL, capture_output=True, text=True, encoding='utf-8', timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_static_viewer_generates_from_fixture_without_ai(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            output = workspace / 'eval-0/with_skill/outputs'
            output.mkdir(parents=True)
            (output / 'result.txt').write_text('閲覧ツールの接続確認用データ', encoding='utf-8')
            report = workspace / 'review.html'
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', '-B', 'eval-viewer/generate_review.py',
                 str(workspace), '--skill-name', 'sample', '--static', str(report)],
                cwd=SKILL, capture_output=True, text=True, encoding='utf-8', timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            page = report.read_text(encoding='utf-8')
            embedded = re.search(r'const EMBEDDED_DATA = (\{[^\n]*\});', page)
            self.assertIsNotNone(embedded)
            data = json.loads(embedded.group(1))
            self.assertEqual(data['skill_name'], 'sample')
            self.assertEqual(data['runs'][0]['outputs'][0]['content'], '閲覧ツールの接続確認用データ')


if __name__ == '__main__':
    unittest.main()
