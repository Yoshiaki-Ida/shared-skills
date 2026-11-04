#!/usr/bin/env python3
"""Validate an Agent Skill using UTF-8 on every platform."""

import re
import sys
from pathlib import Path

import yaml

MAX_SKILL_NAME_LENGTH = 64
ALLOWED_PROPERTIES = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}


def validate_skill(skill_path: str) -> tuple[bool, str]:
    skill_dir = Path(skill_path)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return False, "SKILL.md not found"

    try:
        content = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return False, f"SKILL.md must be UTF-8: {exc}"

    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return False, f"Invalid YAML in frontmatter: {exc}"

    if not isinstance(frontmatter, dict):
        return False, "Frontmatter must be a YAML dictionary"

    unexpected = set(frontmatter) - ALLOWED_PROPERTIES
    if unexpected:
        return False, "Unexpected frontmatter key(s): " + ", ".join(sorted(unexpected))

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name.strip():
        return False, "Missing or invalid 'name' in frontmatter"
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        return False, "Name must use lowercase letters, digits, and single hyphens"
    if len(name) > MAX_SKILL_NAME_LENGTH:
        return False, f"Name is longer than {MAX_SKILL_NAME_LENGTH} characters"
    if skill_dir.name != name:
        return False, f"Directory name '{skill_dir.name}' must match skill name '{name}'"

    if not isinstance(description, str) or not description.strip():
        return False, "Missing or invalid 'description' in frontmatter"
    if len(description.strip()) > 1024:
        return False, "Description is longer than 1024 characters"
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets"

    if re.search(r"(?m)^[ ]{0,3}\[TODO:[^\n]*\][ \t]*$", content[match.end() :]):
        return False, "Skill instructions contain an unfinished TODO placeholder"

    return True, "Skill is valid!"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python quick_validate.py <skill_directory>")
        raise SystemExit(1)

    valid, message = validate_skill(sys.argv[1])
    print(message)
    raise SystemExit(0 if valid else 1)
