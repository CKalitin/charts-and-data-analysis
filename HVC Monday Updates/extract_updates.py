"""
Extract Monday.com updates from a saved HTML file into a clean Markdown document.
Images are placed inline at their correct positions relative to the text content.
"""

import os
import re
import sys
import glob
import time
import shutil
import webbrowser
from urllib.parse import unquote
from bs4 import BeautifulSoup, NavigableString, Tag

# Max seconds to wait for each image download before timing out
IMAGE_DOWNLOAD_WAIT_TIME = 5


def get_image_ext(img_tag):
    """Always use .png for local image files."""
    return 'png'

def extract_text_from_element(element):
    """Recursively extract text from an element, handling <br> as newlines and inline formatting."""
    if isinstance(element, NavigableString):
        return str(element)
    if isinstance(element, Tag):
        if element.name == 'br':
            return '\n'
        if element.name == 'img':
            return ''  # Skip images in text extraction
        if element.name == 'iframe':
            return ''  # Skip iframes
        if element.name == 'a':
            href = element.get('href', '')
            text = ''.join(extract_text_from_element(c) for c in element.children)
            # Handle @mentions
            if 'user_mention_editor' in (element.get('class') or []):
                return text
            if href and text.strip():
                return f'[{text.strip()}]({href})'
            return text
        if element.name == 'strong':
            text = ''.join(extract_text_from_element(c) for c in element.children)
            if text.strip():
                return f'**{text}**'
            return text
        if element.name == 'em':
            text = ''.join(extract_text_from_element(c) for c in element.children)
            if text.strip():
                return f'*{text}*'
            return text
        if element.name == 'div':
            # Inline divs (used in mentions etc.)
            return ''.join(extract_text_from_element(c) for c in element.children)
        # Default: recurse into children
        return ''.join(extract_text_from_element(c) for c in element.children)
    return ''


def process_content_area(content_div, images_dir, image_rel_path='../images'):
    """
    Walk through a content div's children in document order.
    Returns a list of markdown content blocks (text and image refs) in order.
    """
    blocks = []

    def walk_children(parent):
        """Walk children, yielding (type, data) tuples in document order."""
        for child in parent.children:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    blocks.append(('text', text))
            elif isinstance(child, Tag):
                # Content image (has data-asset_id, no avatar test id)
                if child.name == 'img' and child.get('data-asset_id'):
                    asset_id = child.get('data-asset_id')
                    width = child.get('width')
                    height = child.get('height')
                    ext = get_image_ext(child)

                    local_filename = f"image_{asset_id}.{ext}"

                    if width and height:
                        img_md = f'<img src="{image_rel_path}/{local_filename}" width="{width}" height="{height}">'
                    else:
                        img_md = f'![]({image_rel_path}/{local_filename})'

                    blocks.append(('image', img_md))

                elif child.name == 'p':
                    # Process <p> tag - may contain text and/or images
                    p_parts = []
                    for p_child in child.children:
                        if isinstance(p_child, Tag) and p_child.name == 'img' and p_child.get('data-asset_id'):
                            # Flush accumulated text before the image
                            text_so_far = ''.join(p_parts).strip()
                            if text_so_far:
                                blocks.append(('text', text_so_far))
                                p_parts = []

                            asset_id = p_child.get('data-asset_id')
                            width = p_child.get('width')
                            height = p_child.get('height')
                            ext = get_image_ext(p_child)

                            local_filename = f"image_{asset_id}.{ext}"

                            if width and height:
                                img_md = f'<img src="{image_rel_path}/{local_filename}" width="{width}" height="{height}">'
                            else:
                                img_md = f'![]({image_rel_path}/{local_filename})'

                            blocks.append(('image', img_md))
                        else:
                            p_parts.append(extract_text_from_element(p_child))

                    remaining = ''.join(p_parts).strip()
                    if remaining:
                        blocks.append(('text', remaining))

                elif child.name == 'div' and '_JvxH' in (child.get('class') or []):
                    # File attachment div - extract link
                    link = child.find('a')
                    if link:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        if href and text:
                            blocks.append(('text', f'[{text}]({href})'))

                elif child.name in ('div', 'span'):
                    # Recurse into generic containers
                    walk_children(child)

    walk_children(content_div)
    return blocks


def clean_text_block(text):
    """Clean up text blocks for markdown output."""
    # Normalize whitespace
    text = text.replace('\xa0', ' ')
    # Clean up multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip leading/trailing whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    return text.strip()


def blocks_to_markdown(blocks):
    """Convert a list of (type, data) blocks into clean markdown text."""
    md_parts = []
    for block_type, data in blocks:
        if block_type == 'text':
            cleaned = clean_text_block(data)
            if cleaned:
                md_parts.append(cleaned)
        elif block_type == 'image':
            md_parts.append(f'\n{data}\n')

    result = '\n\n'.join(md_parts)
    # Clean up excessive newlines around images
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def extract_attached_images(container, image_rel_path, exclude_replies=False):
    """Extract images from post-additional-asset-component-wrapper divs (file attachments)."""
    blocks = []
    wrappers = container.find_all('div', class_='post-additional-asset-component-wrapper')
    for wrapper in wrappers:
        # Skip attachments inside reply-components when extracting post-level images
        if exclude_replies and wrapper.find_parent('div', {'data-testid': 'reply-component'}):
            continue
        img = wrapper.find('img', attrs={'data-asset_id': True})
        if img:
            asset_id = img.get('data-asset_id')
            width = img.get('width')
            height = img.get('height')
            ext = get_image_ext(img)
            local_filename = f"image_{asset_id}.{ext}"
            if width and height:
                img_md = f'<img src="{image_rel_path}/{local_filename}" width="{width}" height="{height}">'
            else:
                img_md = f'![]({image_rel_path}/{local_filename})'
            blocks.append(('image', img_md))
    return blocks


def extract_post_content(post, images_dir, image_rel_path='../images'):
    """Extract the main content of a post (not replies)."""
    # Extract author from the post header (first avatar only)
    header = post.find('div', {'data-testid': 'post-header-container'})
    author = 'Unknown Author'
    if header:
        author_img = header.find('img', {'data-testid': 'avatar-content'})
        if author_img:
            author = author_img.get('alt', 'Unknown Author')

    # Extract date from the post header
    date = 'Not available'
    if header:
        date_elem = header.find('div', {'data-testid': 'post-timestamp'})
        if date_elem:
            date = date_elem.get_text().strip()

    # Find the main post renderer (first one, not replies)
    content_div = None
    all_renderers = post.find_all('div', {'data-testid': 'post-renderer-component'})
    if all_renderers:
        main_renderer = all_renderers[0]
        content_div = main_renderer.find('div', class_=lambda c: c and 'agPPc' in c)

    # Try to find a title
    title = "Untitled"
    if content_div:
        title_span = content_div.find('span', style=lambda s: s and 'font-size' in str(s) and '24' in str(s))
        if title_span:
            strong = title_span.find('strong')
            if strong:
                title = strong.get_text().strip()
            else:
                title = title_span.get_text().strip()

    # Process content in document order
    content_blocks = []
    if content_div:
        content_blocks = process_content_area(content_div, images_dir, image_rel_path)

    # Also capture post-attached images (file attachments, excluding replies)
    content_blocks.extend(extract_attached_images(post, image_rel_path, exclude_replies=True))

    return {
        'author': author,
        'date': date,
        'title': title,
        'content_blocks': content_blocks,
    }


def extract_replies(post, images_dir, image_rel_path='../images'):
    """Extract all reply contents from a post."""
    replies = []
    reply_divs = post.find_all('div', {'data-testid': 'reply-component'})

    for reply_div in reply_divs:
        # Extract reply author
        author_img = reply_div.find('img', {'data-testid': 'avatar-content'})
        author = author_img.get('alt', 'Unknown Author') if author_img else 'Unknown Author'
        # Clean up author names like "Aarjav Jain - Electrical Director" -> "Aarjav Jain"
        if ' - ' in author:
            author = author.split(' - ')[0]

        # Extract reply date
        date_elem = reply_div.find('div', {'data-testid': 'post-timestamp'})
        date = date_elem.get_text().strip() if date_elem else ''

        # Find reply content
        renderer = reply_div.find('div', {'data-testid': 'post-renderer-component'})
        content_blocks = []
        if renderer:
            content_div = renderer.find('div', class_=lambda c: c and 'agPPc' in c)
            if content_div:
                content_blocks = process_content_area(content_div, images_dir, image_rel_path)

        # Also capture reply-attached images
        content_blocks.extend(extract_attached_images(reply_div, image_rel_path))

        replies.append({
            'author': author,
            'date': date,
            'content_blocks': content_blocks,
        })

    return replies


def get_asset_ids_from_html(html_content):
    """Extract all unique asset IDs with their extensions in order of appearance.
    Returns list of (asset_id, extension) tuples."""
    soup = BeautifulSoup(html_content, 'html.parser')
    seen = set()
    unique = []
    for img in soup.find_all('img', attrs={'data-asset_id': True}):
        aid = img.get('data-asset_id')
        if aid not in seen:
            seen.add(aid)
            ext = get_image_ext(img)
            unique.append((aid, ext))
    return unique


def get_image_url(html_content, asset_id):
    """Extract the full image URL for an asset ID from the HTML."""
    # Try to find the exact src URL for this asset
    pattern = rf'src="(https?://[^"]+/resources/{asset_id}/[^"]+)"'
    match = re.search(pattern, html_content)
    if match:
        return match.group(1)
    return None


def download_missing_images(html_content, images_dir, asset_ids, wait_time=IMAGE_DOWNLOAD_WAIT_TIME):
    """
    For each asset ID missing a local image, open the Monday.com URL in the
    browser (which has auth cookies), wait for the download, and move it
    into the images dir with the correct name.
    """
    downloads_dir = os.path.expanduser('~/Downloads')
    poll_interval = 0.5
    max_polls = int(wait_time / poll_interval)

    missing = []
    for aid, ext in asset_ids:
        target = os.path.join(images_dir, f"image_{aid}.{ext}")
        if not os.path.exists(target):
            missing.append((aid, ext))

    if not missing:
        print("All images present locally.")
        return

    print(f"\n{len(missing)} image(s) need downloading. Opening in browser...")
    print("(Make sure you are logged into Monday.com in your default browser)\n")

    for aid, ext in missing:
        url = get_image_url(html_content, aid)
        target = os.path.join(images_dir, f"image_{aid}.{ext}")

        # Extract the expected download filename from the URL
        url_filename = os.path.basename(url.split('?')[0]) if url else ''
        # URL-decode the filename (e.g. %20 -> space)
        url_filename = unquote(url_filename)

        # Snapshot all image files in Downloads before opening
        img_exts = ('*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.JPG', '*.PNG')
        before = set()
        for pattern in img_exts:
            before |= set(glob.glob(os.path.join(downloads_dir, pattern)))

        print(f"  Opening: {url}")
        webbrowser.open(url)

        # Wait for a new image file to appear (up to wait_time seconds)
        new_file = None
        for _ in range(max_polls):
            time.sleep(0.5)
            after = set()
            for pattern in img_exts:
                after |= set(glob.glob(os.path.join(downloads_dir, pattern)))
            diff = after - before
            if diff:
                # Pick the newest one
                new_file = max(diff, key=os.path.getmtime)
                # Make sure download is finished (file size stable)
                size1 = os.path.getsize(new_file)
                time.sleep(0.5)
                size2 = os.path.getsize(new_file)
                if size1 == size2 and size1 > 0:
                    break
                new_file = None  # Still downloading

        if new_file:
            shutil.move(new_file, target)
            print(f"  Saved:   image_{aid}.{ext} ({os.path.getsize(target):,} bytes)")
        else:
            print(f"  TIMEOUT: Could not detect download for asset {aid}")
            print(f"           Please download manually from: {url}")
            print(f"           Save as: {target}")

    print()


def extract_updates(html_file, output_md, images_dir='images', image_rel_path='../images'):
    """Main extraction function."""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all top-level posts
    posts = soup.find_all('div', {'data-testid': 'post-component'})
    print(f"Found {len(posts)} posts")

    # Build asset ID list and download any missing images
    asset_ids = get_asset_ids_from_html(html_content)
    print(f"Found {len(asset_ids)} unique content images in HTML")
    download_missing_images(html_content, images_dir, asset_ids)

    with open(output_md, 'w', encoding='utf-8') as md_file:
        for post_index, post in enumerate(posts, 1):
            # Extract main post content
            post_data = extract_post_content(post, images_dir, image_rel_path)

            # Write post header
            md_file.write(f"# {post_data['title']}\n\n")
            md_file.write(f"**Author:** {post_data['author']}\n\n")
            md_file.write(f"**Date:** {post_data['date']}\n\n")

            # Write content with inline images
            content_md = blocks_to_markdown(post_data['content_blocks'])
            if content_md:
                md_file.write(content_md + '\n\n')

            # Extract and write replies
            replies = extract_replies(post, images_dir, image_rel_path)

            for reply in replies:
                reply_content = blocks_to_markdown(reply['content_blocks'])
                if reply_content:
                    reply_header = f"> **{reply['author']}**"
                    if reply['date']:
                        reply_header += f" ({reply['date']})"
                    md_file.write(f"{reply_header}\n>\n")
                    # Indent reply content with >
                    for line in reply_content.split('\n'):
                        md_file.write(f"> {line}\n")
                    md_file.write('\n')

            md_file.write('---\n\n')

    # Report on image status
    print(f"\nGenerated: {output_md}")
    missing = [(aid, ext) for aid, ext in asset_ids if not os.path.exists(os.path.join(images_dir, f"image_{aid}.{ext}"))]
    if missing:
        print(f"\nWarning: {len(missing)} images still missing after download attempt:")
        for aid, ext in missing:
            url = get_image_url(html_content, aid)
            print(f"  - image_{aid}.{ext}  ->  {url}")
    else:
        print("All images present locally!")


if __name__ == "__main__":
    # Ordered lists for PCB and Research categories.
    # Files that don't exist in the html folders are silently skipped.
    PCB_ORDER = [
        "Schematic",
        "Power Schematic Page",
        "MCU Schematic Page",
        "LV Control Schematic Page",
        "Contactor Control Schematic Page",
        "E-Stop Level Shifting Schematic Page",
        "CAN Transceiver Schematic",
        "Fan Control Schematic Page",
        "HV Current Sensor Schematic Page",
        "Startup Relays / Power Prioritizer Schematic",
        "LV Current Sensor Schematic Page",
        "Discharge Relay Schematic Page",
        "DCDC Selection / Schematic Page",
        "Connections & Junction Board Interface",
        "Driver Startup Switch Pinout",
        "Component Layout + Routing",
        "Supplemental Inline Fuse",
    ]

    RESEARCH_ORDER = [
        "Failure mode analysis reflection",
        "DRO",
        "LVS Current Sensor Investigation",
        "Startup Switch Testing",
        "Brightside LVS Current Consumption",
        "Pre/Discharge Resistors Mounted on HVC",
        "ECU rev 2.0 Design Document Notes",
        "Swap Relay vs. Power Prioritizer",
        "Current Sensor Options",
        "Power Integrations DCDC Testing",
    ]

    def normalize(name):
        """Normalize a name for fuzzy matching: lowercase, strip punctuation."""
        n = name.lower()
        n = n.replace('_', ' ').replace('/', ' ').replace('&', ' ').replace('+', ' ')
        n = re.sub(r'[^a-z0-9 ]', '', n)
        n = re.sub(r'\s+', ' ', n).strip()
        return n

    def match_file_to_order(filename_base, order_list):
        """
        Match an HTML filename (without extension) to an entry in the order list.
        Returns the 1-based index if matched, or None.
        Uses word-overlap scoring, preferring the most specific (longest) match.
        """
        norm_file = normalize(filename_base)
        file_words = set(norm_file.split())

        best_idx = None
        best_score = 0
        best_len = 0

        for i, entry in enumerate(order_list, 1):
            norm_entry = normalize(entry)
            entry_words = set(norm_entry.split())

            if not entry_words:
                continue

            common = file_words & entry_words
            score = len(common) / len(entry_words)

            # Require at least 60% word overlap
            if score >= 0.6:
                # Prefer higher score, then longer match (more specific)
                if score > best_score or (score == best_score and len(entry_words) > best_len):
                    best_score = score
                    best_idx = i
                    best_len = len(entry_words)

        return best_idx

    images_dir = 'images'
    os.makedirs(images_dir, exist_ok=True)

    # Category definitions: (html_subdir, order_list, output_subdir)
    categories = [
        ('html/pcb',      PCB_ORDER,      'output/pcb'),
        ('html/research',  RESEARCH_ORDER, 'output/research'),
    ]

    for html_subdir, order_list, output_subdir in categories:
        os.makedirs(output_subdir, exist_ok=True)

        # Collect HTML files in this subfolder
        html_files = sorted(glob.glob(os.path.join(html_subdir, '*.html')))
        if not html_files:
            print(f"No .html files found in {html_subdir}/")
            continue

        # Match each file to its position in the order list
        ordered_files = []  # (sort_key, html_path, display_name)
        for html_file in html_files:
            base = os.path.splitext(os.path.basename(html_file))[0]
            idx = match_file_to_order(base, order_list)
            if idx is not None:
                ordered_files.append((idx, html_file, base))
            else:
                # Unmatched files go at the end, sorted alphabetically
                ordered_files.append((len(order_list) + 1, html_file, base))

        ordered_files.sort(key=lambda x: (x[0], x[2]))

        # Image relative path from output subdir back to images/
        # output/pcb/ -> ../../images
        image_rel_path = '../../images'

        for seq_num, (sort_key, html_file, base) in enumerate(ordered_files, 1):
            prefix = f"{seq_num:02d}"
            output_md = os.path.join(output_subdir, f"{prefix} - {base}_Updates.md")
            print(f"\n{'='*60}")
            print(f"Processing: {html_file} -> {output_md}")
            print(f"{'='*60}")
            extract_updates(html_file, output_md, images_dir, image_rel_path)

    # Write out a file listing all images that are still missing
    # Also find which output .md file and line number references each image
    all_missing = []
    for html_subdir, order_list, output_subdir in categories:
        category = os.path.basename(html_subdir)  # 'pcb' or 'research'
        html_files = sorted(glob.glob(os.path.join(html_subdir, '*.html')))
        for html_file in html_files:
            base = os.path.splitext(os.path.basename(html_file))[0]
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            for aid, ext in get_asset_ids_from_html(html_content):
                target = os.path.join(images_dir, f"image_{aid}.{ext}")
                if not os.path.exists(target):
                    url = get_image_url(html_content, aid)
                    all_missing.append((aid, url, base, category))

    # Build a lookup: asset_id -> [(md_file, line_number), ...]
    md_locations = {}
    for output_subdir_path in ['output/pcb', 'output/research']:
        for md_path in glob.glob(os.path.join(output_subdir_path, '*.md')):
            with open(md_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    match = re.search(r'image_(\d+)\.\w+', line)
                    if match:
                        found_aid = match.group(1)
                        md_locations.setdefault(found_aid, []).append((md_path, line_num))

    missing_file = 'missing_images.txt'
    if all_missing:
        # Deduplicate while preserving order
        seen = set()
        unique_missing = []
        for aid, url, source, category in all_missing:
            if aid not in seen:
                seen.add(aid)
                unique_missing.append((aid, url, source, category))
        with open(missing_file, 'w', encoding='utf-8') as f:
            for aid, url, source, category in unique_missing:
                f.write(f"{aid}\n  Category: {category}\n  Source: {source}\n  {url}\n")
                for md_path, line_num in md_locations.get(aid, []):
                    f.write(f"  Referenced in: {md_path} (line {line_num})\n")
                f.write("\n")
        print(f"\n{len(unique_missing)} missing image(s) written to {missing_file}")
    else:
        # Remove stale file if all images are present
        if os.path.exists(missing_file):
            os.remove(missing_file)
        print("\nAll images downloaded successfully!")