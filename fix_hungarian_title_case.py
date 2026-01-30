#!/usr/bin/env python3
"""
Fix Hungarian Title Case to Sentence Case

Converts English-style title case (every word capitalized) to Hungarian sentence case
(only first word and proper nouns capitalized) in markdown files.

Usage:
    python fix_hungarian_title_case.py --dry-run  # Preview changes
    python fix_hungarian_title_case.py            # Apply changes
    python fix_hungarian_title_case.py --files "file1.md,file2.md"  # Specific files
"""

import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from hungarian_proper_nouns import is_proper_noun, is_common_noun, MULTI_WORD_PROPER_NOUNS

class HungarianTitleCaseFixer:
    """
    Fix English-style title case in Hungarian markdown files.
    """

    def __init__(self, dry_run=True, verbose=False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.total_changes = 0

    def fix_text_to_sentence_case(self, text, is_first_word=False):
        """
        Convert a piece of text to Hungarian sentence case.

        Args:
            text: Text to convert
            is_first_word: If True, this is the first word of a sentence/heading

        Returns:
            str: Fixed text
        """
        # Note: Multi-word proper nouns are now handled by including each word
        # separately in PROPER_NOUNS (e.g., both "Guru" and "Rinpoche")

        words = text.split()
        fixed_words = []

        # Track if we've seen the actual first word (skip numbers/punctuation)
        seen_first_actual_word = False

        for i, word in enumerate(words):
            # Preserve markdown formatting
            prefix = ''
            suffix = ''
            core_word = word

            # Extract markdown bold/italic
            while core_word.startswith('**') or core_word.startswith('*'):
                if core_word.startswith('**'):
                    prefix += '**'
                    core_word = core_word[2:]
                elif core_word.startswith('*'):
                    prefix += '*'
                    core_word = core_word[1:]

            while core_word.endswith('**') or core_word.endswith('*'):
                if core_word.endswith('**'):
                    suffix = '**' + suffix
                    core_word = core_word[:-2]
                elif core_word.endswith('*'):
                    suffix = '*' + suffix
                    core_word = core_word[:-1]

            # Check if this is a number, punctuation, or list marker (like "1.", "2)", "A.", etc.)
            is_number_or_punct = bool(re.match(r'^[\d\W]+$', core_word) or re.match(r'^[A-Z]\.$', core_word))

            # Determine if this should be treated as "first word"
            is_effective_first_word = (is_first_word and not seen_first_actual_word and not is_number_or_punct)

            if not is_number_or_punct:
                seen_first_actual_word = True

            # First actual word of sentence/heading - capitalize
            if is_effective_first_word:
                # Capitalize first letter, preserve rest
                if core_word:
                    if is_proper_noun(core_word):
                        # Keep proper noun as-is
                        fixed_word = core_word
                    else:
                        # Capitalize first letter, lowercase rest
                        fixed_word = core_word[0].upper() + core_word[1:].lower() if len(core_word) > 1 else core_word.upper()
                else:
                    fixed_word = core_word

            # Check if it's a proper noun
            elif is_proper_noun(core_word):
                fixed_word = core_word  # Keep as-is

            # Explicitly a common noun
            elif is_common_noun(core_word):
                fixed_word = core_word.lower()

            # Number or punctuation - keep as-is
            elif is_number_or_punct:
                fixed_word = core_word

            # Default: lowercase
            else:
                fixed_word = core_word.lower()

            fixed_words.append(prefix + fixed_word + suffix)

        return ' '.join(fixed_words)

    def fix_heading(self, heading_text):
        """
        Convert heading to Hungarian sentence case.

        Preserves:
        - Markdown formatting (**bold**, *italic*)
        - Parenthetical expressions
        - Proper nouns
        """
        # Handle links in headings: [Text](url)
        link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        parts = []
        last_end = 0

        for match in re.finditer(link_pattern, heading_text):
            # Add text before link
            if match.start() > last_end:
                before_text = heading_text[last_end:match.start()]
                is_first = (last_end == 0)
                parts.append(self.fix_text_to_sentence_case(before_text, is_first_word=is_first))

            # Fix link text but preserve URL
            link_text = match.group(1)
            url = match.group(2)
            fixed_link_text = self.fix_text_to_sentence_case(link_text, is_first_word=(last_end == 0))
            parts.append(f'[{fixed_link_text}]({url})')

            last_end = match.end()

        # Add remaining text
        if last_end < len(heading_text):
            remaining = heading_text[last_end:]
            is_first = (last_end == 0)
            parts.append(self.fix_text_to_sentence_case(remaining, is_first_word=is_first))

        result = ''.join(parts)
        return result

    def fix_navigation_footer(self, line):
        """
        Fix navigation pattern: < [Text](path) | [Text](path) >
        """
        pattern = r'<\s*\[(.+?)\]\((.+?)\)\s*\|\s*\[(.+?)\]\((.+?)\)\s*>'

        def replace_nav(match):
            left_text, left_path, right_text, right_path = match.groups()
            new_left = self.fix_heading(left_text)
            new_right = self.fix_heading(right_text)
            return f'< [{new_left}]({left_path}) | [{new_right}]({right_path}) >'

        return re.sub(pattern, replace_nav, line)

    def fix_toc_entry(self, line):
        """
        Fix TOC list items: - [Text](path)
        """
        pattern = r'^(\s*-\s+)\[(.+?)\]\((.+?)\)'

        def replace_toc(match):
            indent, text, path = match.groups()
            new_text = self.fix_heading(text)
            return f'{indent}[{new_text}]({path})'

        return re.sub(pattern, replace_toc, line)

    def looks_like_title_case(self, text):
        """
        Check if text looks like it's in title case (multiple capitalized words).
        """
        # Remove markdown formatting
        clean_text = re.sub(r'\*\*?', '', text)
        # Remove parenthetical content
        clean_text = re.sub(r'\([^)]+\)', '', clean_text)

        words = clean_text.split()
        if len(words) < 2:
            return False

        # Count capitalized words (excluding first word)
        capitalized = sum(1 for w in words[1:] if w and w[0].isupper())

        # If more than half of the remaining words are capitalized, it's likely title case
        return capitalized > len(words[1:]) * 0.5

    def fix_inline_link(self, line):
        """
        Fix inline links: [text](path)
        Be conservative - only fix if clearly title case
        """
        pattern = r'\[([^\]]{10,})\]\(([^)]+)\)'

        def replace_link(match):
            text, path = match.groups()
            # Only fix if looks like title case
            if self.looks_like_title_case(text):
                new_text = self.fix_heading(text)
                return f'[{new_text}]({path})'
            return match.group(0)

        return re.sub(pattern, replace_link, line)

    def process_file(self, file_path):
        """
        Process a single markdown file.

        Returns:
            dict: Information about changes made
        """
        file_path = Path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            return {
                'file_path': str(file_path),
                'error': str(e),
                'changes': []
            }

        new_lines = []
        file_changes = []

        for line_num, line in enumerate(lines, 1):
            original_line = line

            # Check for heading (starts with #)
            if line.strip().startswith('#'):
                match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
                if match:
                    level, heading = match.groups()
                    new_heading = self.fix_heading(heading)
                    if new_heading != heading:
                        line = f'{level} {new_heading}\n'

            # Check for navigation footer (pattern: < [text](url) | [text](url) >)
            elif re.search(r'<\s*\[.+?\]\(.+?\)\s*\|\s*\[.+?\]\(.+?\)\s*>', line):
                new_line = self.fix_navigation_footer(line)
                if new_line != line:
                    line = new_line

            # Check for TOC entry (list item with link)
            elif re.match(r'^\s*-\s+\[', line):
                new_line = self.fix_toc_entry(line)
                if new_line != line:
                    line = new_line

            # Check for inline links (conservative - only obvious title case)
            elif '[' in line and '](' in line:
                new_line = self.fix_inline_link(line)
                if new_line != line:
                    line = new_line

            # Track changes
            if line != original_line:
                file_changes.append({
                    'line_num': line_num,
                    'old': original_line.strip(),
                    'new': line.strip()
                })
                self.total_changes += 1

            new_lines.append(line)

        return {
            'file_path': str(file_path),
            'changes': file_changes,
            'new_content': ''.join(new_lines)
        }

    def process_all_files(self, specific_files=None):
        """
        Process all Hungarian markdown files or specific files.

        Args:
            specific_files: Optional list of specific file paths

        Returns:
            list: All changes made
        """
        if specific_files:
            md_files = [Path(f) for f in specific_files]
        else:
            hu_dir = Path(__file__).parent / 'languages' / 'hu'
            md_files = sorted(hu_dir.rglob('*.md'))

        all_changes = []

        print(f"Processing {len(md_files)} files...")
        if self.dry_run:
            print("DRY RUN MODE - No changes will be written\n")

        for md_file in md_files:
            result = self.process_file(md_file)

            if 'error' in result:
                print(f"ERROR processing {result['file_path']}: {result['error']}")
                continue

            if result['changes']:
                all_changes.append(result)

                # Print changes
                try:
                    rel_path = Path(result['file_path']).relative_to(Path.cwd())
                except ValueError:
                    rel_path = Path(result['file_path'])
                print(f"\n{rel_path} ({len(result['changes'])} changes):")

                for change in result['changes'][:5]:  # Show first 5 changes per file
                    print(f"  Line {change['line_num']}:")
                    print(f"    - {change['old']}")
                    print(f"    + {change['new']}")

                if len(result['changes']) > 5:
                    print(f"  ... and {len(result['changes']) - 5} more changes")

                # Write changes if not dry run
                if not self.dry_run:
                    with open(result['file_path'], 'w', encoding='utf-8') as f:
                        f.write(result['new_content'])

        return all_changes

def main():
    parser = argparse.ArgumentParser(
        description='Fix Hungarian title case to sentence case in markdown files'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without writing files'
    )
    parser.add_argument(
        '--files',
        type=str,
        help='Comma-separated list of specific files to process'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    specific_files = None
    if args.files:
        specific_files = [f.strip() for f in args.files.split(',')]

    fixer = HungarianTitleCaseFixer(dry_run=args.dry_run, verbose=args.verbose)
    changes = fixer.process_all_files(specific_files=specific_files)

    # Summary
    print("\n" + "=" * 60)
    print(f"Total files with changes: {len(changes)}")
    print(f"Total changes made: {fixer.total_changes}")

    if args.dry_run:
        print("\nThis was a DRY RUN. No files were modified.")
        print("Run without --dry-run to apply changes.")
    else:
        print("\nChanges have been written to files.")
        print("Run 'python regenerate_all_anchors.py' to update anchor files.")

    return 0 if not changes or not args.dry_run else 1

if __name__ == '__main__':
    sys.exit(main())
