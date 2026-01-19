#!/usr/bin/env python3
"""
Fix self-referencing headings in README.md files.

This script identifies markdown headings that link to themselves and either:
1. Updates them to point to corresponding subdirectory README.md files
2. Removes the link entirely if no subdirectory exists

Exception: The first heading in each README.md file is always preserved unchanged.
"""

import argparse
import logging
import os
import re
import shutil
from pathlib import Path
from typing import List, Tuple, Optional


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('fix_headings.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def find_self_referencing_headings(content: str, file_path: Path, repo_root: Path) -> List[Tuple[int, str, str, str, str]]:
    """
    Find all self-referencing headings in the content.

    Returns: List of tuples (line_number, full_line, heading_level, heading_text, url)
    """
    lines = content.split('\n')
    self_refs = []

    # Pattern to match headings with links
    heading_pattern = re.compile(r'^(#{1,6})\s+\[(.*?)\]\((https://github\.com/[^/]+/[^/]+/blob/master/([^)]+))\)$')

    # Normalize the current file path for comparison (relative to repo root)
    try:
        normalized_file = str(file_path.relative_to(repo_root))
    except ValueError:
        # If file is not under repo_root, use absolute path
        normalized_file = str(file_path)

    logger.debug(f"Normalized file path: {normalized_file}")
    logger.debug(f"Total lines: {len(lines)}")

    for i, line in enumerate(lines):
        match = heading_pattern.match(line.strip())
        if match:
            level = match.group(1)
            text = match.group(2)
            url = match.group(3)
            url_path = match.group(4)

            logger.debug(f"Line {i+1}: Found heading link")
            logger.debug(f"  url_path: {url_path}")

            # Normalize URL path for comparison (remove anchor)
            normalized_url_path = url_path.split('#')[0]

            # Check if URL points to the same file (self-reference)
            if normalized_url_path.endswith('README.md'):
                logger.debug(f"  normalized_url_path: {normalized_url_path}")
                logger.debug(f"  Comparison: '{normalized_file}' == '{normalized_url_path}' -> {normalized_file == normalized_url_path}")

                if normalized_file == normalized_url_path:
                    self_refs.append((i, line, level, text, url_path))
                    logger.debug(f"Found self-reference at line {i+1}: {text[:50]}...")

    return self_refs


def extract_subdirectory_link(lines: List[str], start_line: int, window_size: int = 10) -> Optional[str]:
    """
    Extract a subdirectory README.md link from the next few lines after a heading.

    Looks for links like: ](dirname/README.md) or ](01_dirname/README.md#anchor)
    Ignores parent directory links (../) but NOT image links (as images may be linked to READMEs).
    """
    # Pattern to find relative subdirectory README.md links
    link_pattern = re.compile(r'\]\(([^/)][^)]*?/README\.md[^)]*)\)')

    end_line = min(start_line + window_size, len(lines))

    logger.debug(f"Searching for subdirectory link from line {start_line+1} to {end_line}")

    for i in range(start_line + 1, end_line):
        line = lines[i]

        logger.debug(f"  Checking line {i+1}: {line.strip()[:80]}...")

        # Skip lines with parent directory links
        if '../' in line:
            logger.debug(f"    Skipping (contains ../)")
            continue

        match = link_pattern.search(line)
        if match:
            link = match.group(1)

            # Skip if this is a full URL (starts with http)
            if link.startswith('http'):
                logger.debug(f"    Skipping (full URL): {link[:50]}...")
                continue

            # Extract just the path before any anchor
            base_link = link.split('#')[0] if '#' in link else link
            logger.debug(f"    Found subdirectory link: {base_link}")
            return base_link

    logger.debug(f"  No subdirectory link found in window")
    return None


def fix_heading(level: str, text: str, subdirectory_link: Optional[str]) -> str:
    """
    Generate the corrected heading line.

    With subdirectory: ## [Text](subdirectory/README.md)
    Without subdirectory: ## Text
    """
    if subdirectory_link:
        return f"{level} [{text}]({subdirectory_link})"
    else:
        return f"{level} {text}"


def process_readme_file(file_path: Path, repo_root: Path, apply_changes: bool = False) -> dict:
    """
    Process a single README.md file to fix self-referencing headings.

    Returns: Dictionary with statistics about changes made
    """
    logger.info(f"\nProcessing: {file_path}")

    # Read file content with UTF-8 encoding
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return {'error': str(e)}

    lines = content.split('\n')
    original_line_count = len(lines)

    # Find all self-referencing headings
    self_refs = find_self_referencing_headings(content, file_path, repo_root)

    if not self_refs:
        logger.info(f"  No self-referencing headings found")
        return {'file': str(file_path), 'changes': 0}

    logger.info(f"  Found {len(self_refs)} self-referencing heading(s)")

    # Skip the first heading (exception rule)
    if self_refs and self_refs[0][0] == 0:
        logger.info(f"  Skipping first heading (line 1): {self_refs[0][3][:50]}...")
        self_refs = self_refs[1:]

    if not self_refs:
        logger.info(f"  All self-references are first headings (exception rule)")
        return {'file': str(file_path), 'changes': 0}

    # Process each self-referencing heading
    changes = []
    for line_num, original_line, level, text, url_path in self_refs:
        # Look for subdirectory link nearby
        subdirectory_link = extract_subdirectory_link(lines, line_num)

        # Generate the fixed heading
        new_line = fix_heading(level, text, subdirectory_link)

        if subdirectory_link:
            logger.info(f"  Line {line_num + 1}: Will point to subdirectory '{subdirectory_link}'")
        else:
            logger.info(f"  Line {line_num + 1}: Will remove link (no subdirectory)")

        logger.debug(f"    Before: {original_line}")
        logger.debug(f"    After:  {new_line}")

        changes.append((line_num, original_line, new_line))

    # Apply changes if requested
    if apply_changes and changes:
        # Create backup
        backup_path = f"{file_path}.backup"
        try:
            shutil.copy2(file_path, backup_path)
            logger.debug(f"  Created backup: {backup_path}")
        except Exception as e:
            logger.error(f"  Failed to create backup: {e}")
            return {'file': str(file_path), 'error': 'backup_failed'}

        # Apply all changes to the lines
        for line_num, original_line, new_line in changes:
            lines[line_num] = new_line

        # Validate
        if len(lines) != original_line_count:
            logger.error(f"  Line count changed! Restoring from backup")
            shutil.copy2(backup_path, file_path)
            return {'file': str(file_path), 'error': 'line_count_mismatch'}

        # Write modified content
        try:
            new_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            logger.info(f"  ✓ Applied {len(changes)} change(s)")

            # Remove backup on success
            os.remove(backup_path)
        except Exception as e:
            logger.error(f"  Failed to write file: {e}")
            # Restore from backup
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, file_path)
            return {'file': str(file_path), 'error': str(e)}

    return {'file': str(file_path), 'changes': len(changes)}


def find_readme_files(base_path: Path) -> List[Path]:
    """Find all README.md files in the repository."""
    readme_files = list(base_path.rglob('README.md'))
    logger.info(f"Found {len(readme_files)} README.md files")
    return sorted(readme_files)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Fix self-referencing headings in README.md files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (review changes without applying)
  python3 fix_self_referencing_headings.py

  # Apply to single file
  python3 fix_self_referencing_headings.py --file more/08_lineage/README.md --apply

  # Apply to all files
  python3 fix_self_referencing_headings.py --apply
        """
    )

    parser.add_argument(
        '--apply',
        action='store_true',
        help='Actually apply the changes (default is dry-run mode)'
    )

    parser.add_argument(
        '--file',
        type=str,
        help='Process only a specific file (relative to repo root)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Determine base path (script should be run from repo root)
    base_path = Path.cwd()

    if not args.apply:
        logger.info("=" * 70)
        logger.info("DRY RUN MODE - No files will be modified")
        logger.info("Use --apply to actually apply changes")
        logger.info("=" * 70)

    # Find files to process
    if args.file:
        file_path = base_path / args.file
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return 1
        files_to_process = [file_path]
    else:
        files_to_process = find_readme_files(base_path)

    # Process all files
    results = []
    for file_path in files_to_process:
        result = process_readme_file(file_path, base_path, apply_changes=args.apply)
        results.append(result)

    # Summary statistics
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY")
    logger.info("=" * 70)

    total_files = len(results)
    files_with_changes = sum(1 for r in results if r.get('changes', 0) > 0)
    total_changes = sum(r.get('changes', 0) for r in results)
    errors = sum(1 for r in results if 'error' in r)

    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Files with changes: {files_with_changes}")
    logger.info(f"Total headings fixed: {total_changes}")

    if errors:
        logger.warning(f"Errors encountered: {errors}")

    if not args.apply and total_changes > 0:
        logger.info("\nTo apply these changes, run with --apply flag")
    elif args.apply and total_changes > 0:
        logger.info("\n✓ Changes applied successfully!")
        logger.info("Run 'git diff' to review changes")

    return 0


if __name__ == '__main__':
    exit(main())
