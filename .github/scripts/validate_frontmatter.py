#!/usr/bin/env python3
"""Validate that all SKILL.md files have required frontmatter (name, description)."""

from pathlib import Path
import re
import sys


def validate_frontmatter(skill_file: Path) -> tuple[bool, str]:
    """Validate a single SKILL.md file's frontmatter.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        content = skill_file.read_text(encoding='utf-8')
    except Exception as e:
        return False, f"Failed to read file: {e}"
    
    # Check for frontmatter delimiters
    if not content.startswith('---\n'):
        return False, "Missing opening frontmatter delimiter '---'"
    
    # Find the closing delimiter
    rest = content[4:]  # Skip opening '---\n'
    closing_match = re.search(r'\n---\n', rest)
    if not closing_match:
        return False, "Missing closing frontmatter delimiter '---'"
    
    # Extract frontmatter content
    frontmatter = rest[:closing_match.start()]
    
    # Check for required fields
    has_name = re.search(r'^name:\s*\S', frontmatter, re.MULTILINE)
    has_description = re.search(r'^description:\s*\S', frontmatter, re.MULTILINE)
    
    missing = []
    if not has_name:
        missing.append('name')
    if not has_description:
        missing.append('description')
    
    if missing:
        return False, f"Missing required field(s): {', '.join(missing)}"
    
    return True, ""


def main() -> int:
    """Find and validate all SKILL.md files."""
    repo_root = Path(__file__).parent.parent.parent
    skill_files = list(repo_root.glob('skills/*/SKILL.md'))
    
    if not skill_files:
        print("⚠️  No SKILL.md files found")
        return 0
    
    print(f"Validating {len(skill_files)} SKILL.md file(s)...\n")
    
    errors = []
    for skill_file in sorted(skill_files):
        skill_name = skill_file.parent.name
        is_valid, error_msg = validate_frontmatter(skill_file)
        
        if is_valid:
            print(f"✓ {skill_name}")
        else:
            print(f"✗ {skill_name}: {error_msg}")
            errors.append((skill_name, error_msg))
    
    if errors:
        print(f"\n❌ {len(errors)} file(s) failed validation")
        return 1
    
    print(f"\n✅ All {len(skill_files)} SKILL.md files are valid")
    return 0


if __name__ == '__main__':
    sys.exit(main())
