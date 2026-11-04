# Changelog

## 1.1.0

- Add four tailored Skills for Skill creation, safe refactoring, specification recovery, and spec-based pytest generation.
- Preserve pinned upstream files, source hashes, and licenses from Anthropic, GitHub awesome-copilot, and spec-forge.
- Adapt local instructions to the public repository's README and installer.
- Extend the preview-first installer to six Skills and one Agent, including HTML line-ending handling.
- Add provenance, reference, validator, offline-tool, and complete-installation checks.

## 1.0.1

- Treat CRLF/LF-only differences in UTF-8 text as OK without overwriting installed files.
- Preserve strict conflict detection for content, whitespace, case, and encoding differences.
- Back up conflicting installed files before explicit updates; stop before installation if backup fails.
- Document installation acceptance criteria, conflict review, explicit updates, and backup restoration.
- Add regression coverage for line endings, content conflicts, and backup safety.

## 1.0.0

- Initial distribution of two meeting Skills and the Redmine meeting orchestrator.
- Preview-first installer with explicit conflict replacement and no file deletion.
- Includes isolated installer and meeting-to-importer connection tests.