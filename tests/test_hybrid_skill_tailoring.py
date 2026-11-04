import hashlib
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    'safe-refactoring': 2,
    'reverse-engineer-specification': 4,
    'generate-tests-from-spec': 8,
}


class HybridSkillTailoringTests(unittest.TestCase):
    def test_upstream_files_match_pinned_provenance(self):
        for name, count in SKILLS.items():
            skill = ROOT / 'skills/software-development' / name
            provenance = json.loads((skill / 'references/upstream-provenance.json').read_text(encoding='utf-8'))
            with self.subTest(skill=name):
                self.assertRegex(provenance['source_commit'], r'^[0-9a-f]{40}$')
                self.assertEqual(len(provenance['files']), count)
                targets = [item['target'] for item in provenance['files']]
                self.assertEqual(len(targets), len(set(targets)))
                self.assertIn(provenance['license_file'], targets)
                for item in provenance['files']:
                    target = (skill / item['target']).resolve()
                    self.assertTrue(target.is_relative_to(skill.resolve()))
                    self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), item['sha256'])
                self.assertEqual([p.relative_to(skill).as_posix() for p in skill.rglob('SKILL.md')], ['SKILL.md'])

    def test_entry_points_link_to_local_files_and_pinned_version(self):
        for name in SKILLS:
            skill = ROOT / 'skills/software-development' / name
            entry = (skill / 'SKILL.md').read_text(encoding='utf-8')
            provenance = json.loads((skill / 'references/upstream-provenance.json').read_text(encoding='utf-8'))
            with self.subTest(skill=name):
                self.assertIn('name: ' + name + '\n', entry)
                self.assertIn(provenance['source_commit'], entry)
                for relative in re.findall(r'\[[^\]]+\]\(([^)]+)\)', entry):
                    target = (skill / relative).resolve()
                    self.assertTrue(target.is_relative_to(skill.resolve()))
                    self.assertTrue(target.is_file(), relative)

    def test_spec_mode_maps_upstream_shared_references(self):
        skill = ROOT / 'skills/software-development/generate-tests-from-spec'
        original = (skill / 'references/upstream.md').read_text(encoding='utf-8')
        for name in re.findall(r'@\.\./shared/([a-z-]+\.md)', original):
            self.assertTrue((skill / 'references/upstream-shared' / name).is_file(), name)
        for name in ['checklist.md', 'generation-instructions.md', 'template.md']:
            self.assertTrue((skill / 'references' / name).is_file(), name)


if __name__ == '__main__':
    unittest.main()
