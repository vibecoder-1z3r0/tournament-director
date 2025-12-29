#!/usr/bin/env python3
"""
Fix exception constructor calls in database repositories.

AIA EAI Hin R Claude Code [Sonnet 4.5] v1.0
"""

import re
from pathlib import Path

# Patterns to fix
PATTERNS = {
    # NotFoundError(f"Entity with ID {id} not found") -> NotFoundError("Entity", id)
    'notfound': (
        r'raise NotFoundError\(f"(\w+) with ID \{(\w+(?:\.\w+)?)\} not found"\)',
        r'raise NotFoundError("\1", \2)'
    ),
    # DuplicateError(f"Entity with ID {id} already exists") -> DuplicateError("Entity", "id", str(id))
    'duplicate_id': (
        r'raise DuplicateError\(f"(\w+) with ID \{(\w+(?:\.\w+)?)\} already exists"\)',
        r'raise DuplicateError("\1", "id", str(\2))'
    ),
    # DuplicateError(f"Entity with field={value} already exists") -> DuplicateError("Entity", "field", str(value))
    'duplicate_field': (
        r'raise DuplicateError\(f"(\w+) with (\w+)=\{(\w+(?:\.\w+)?)\} already exists"\)',
        r'raise DuplicateError("\1", "\2", str(\3))'
    ),
}

def fix_file(filepath: Path) -> int:
    """Fix exception calls in a single file."""
    content = filepath.read_text()
    original = content
    fixes = 0

    for name, (pattern, replacement) in PATTERNS.items():
        new_content = re.sub(pattern, replacement, content)
        if new_content != content:
            count = len(re.findall(pattern, content))
            fixes += count
            content = new_content
            print(f"  - Fixed {count} {name} calls")

    if content != original:
        filepath.write_text(content)
        return fixes
    return 0

def main():
    """Fix all repository files."""
    repo_dir = Path("src/data/database/repositories")
    total_fixes = 0

    for repo_file in sorted(repo_dir.glob("*.py")):
        if repo_file.name == "__init__.py":
            continue

        print(f"\nProcessing {repo_file.name}...")
        fixes = fix_file(repo_file)
        if fixes:
            total_fixes += fixes
            print(f"  ✅ Fixed {fixes} exception calls")
        else:
            print(f"  ✓ No fixes needed")

    print(f"\n{'='*60}")
    print(f"Total fixes: {total_fixes}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
