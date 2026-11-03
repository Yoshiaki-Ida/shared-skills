# Changelog

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