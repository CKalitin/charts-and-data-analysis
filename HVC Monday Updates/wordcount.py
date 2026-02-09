# Thx Grok https://grok.com/chat/a07be4d5-da41-4257-8409-9ccb8bc86777

import os
import re
import csv
import sys
from pathlib import Path
from io import StringIO

def extract_title_and_content(file_path):
    """Extract title and main content from a Markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Extract the first # heading as the title
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Unknown Title"

        return title, content
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, None

def count_words_in_content(content):
    """Count words in the Markdown content, excluding syntax."""
    if not content:
        return 0

    # Remove Markdown syntax
    content = re.sub(r'^#{1,6}\s.*$', '', content, flags=re.MULTILINE)
    content = re.sub(r'```[\s\S]*?```', '', content)
    content = re.sub(r'`[^`]*`', '', content)
    content = re.sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1', content)
    content = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', '', content)
    content = re.sub(r'\*\*([^\*]*)\*\*', r'\1', content)
    content = re.sub(r'\*([^\*]*)\*', r'\1', content)
    content = re.sub(r'__([^_]*)__', r'\1', content)
    content = re.sub(r'_([^_]*)_', r'\1', content)
    content = re.sub(r'^\s*[-*+]\s', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*\d+\.\s', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\s*>\s', '', content, flags=re.MULTILINE)
    content = re.sub(r'^-{3,}$', '', content, flags=re.MULTILINE)
    content = re.sub(r'^\*{3,}$', '', content, flags=re.MULTILINE)
    content = re.sub(r'<[^>]+>', '', content)

    # Split into words and count non-empty ones
    words = [word.strip() for word in content.split() if word.strip()]
    return len(words)

def scan_directory_for_md_files(directory, category):
    """Scan the directory for .md files and return list of row dicts."""
    directory = Path(directory)
    if not directory.is_dir():
        return []

    md_files = sorted(directory.glob("*.md"))
    rows = []
    for md_file in md_files:
        title, content = extract_title_and_content(md_file)
        if title and content:
            word_count = count_words_in_content(content)
            # Extract the display name from filename: "01 - Schematic_Updates.md" -> "Schematic"
            name = md_file.stem  # e.g. "01 - Schematic_Updates"
            # Strip prefix number and " - " and "_Updates" suffix
            display = re.sub(r'^\d+\s*-\s*', '', name)
            display = re.sub(r'_Updates$', '', display)
            rows.append({
                'category': category,
                'order': name[:2],
                'title': display,
                'words': word_count,
                'path': str(md_file),
            })
    return rows


# Scan both output directories
all_rows = []
all_rows.extend(scan_directory_for_md_files(Path(__file__).parent / "output" / "pcb", "PCB"))
all_rows.extend(scan_directory_for_md_files(Path(__file__).parent / "output" / "research", "Research"))

# Print results
output = StringIO()
writer = csv.writer(output, lineterminator='\n')
writer.writerow(['Category', '#', 'Title', 'Words'])

total_words = 0
for row in all_rows:
    writer.writerow([row['category'], row['order'], row['title'], row['words']])
    total_words += row['words']

writer.writerow([])
writer.writerow(['', '', 'TOTAL', total_words])

csv_output = output.getvalue()
print(csv_output)

# Save to file
output_path = Path(__file__).parent / "output" / "word_counts.csv"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(csv_output)