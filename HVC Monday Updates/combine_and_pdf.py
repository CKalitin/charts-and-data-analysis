"""
Combines all Monday Updates markdown files into one document and generates a PDF.

Step 1: Combine all individual .md files from output/pcb/ and output/research/
        into a single combined_updates.md
Step 2: Convert combined markdown to PDF with images embedded inline.
"""

import re
import base64
from pathlib import Path
import markdown
from xhtml2pdf import pisa

ROOT = Path(__file__).parent
IMAGES_DIR = ROOT / "images"
OUTPUT_MD = ROOT / "output" / "combined_updates.md"
OUTPUT_PDF = ROOT / "output" / "combined_updates.pdf"

def combine_markdown_files():
    """Combine all MD files from output/pcb and output/research into one."""
    combined_parts = []

    for category, folder in [("PCB", "pcb"), ("Research", "research")]:
        cat_dir = ROOT / "output" / folder
        if not cat_dir.is_dir():
            print(f"  Skipping {category}: {cat_dir} not found")
            continue

        # Category header
        combined_parts.append(f"# {category}\n")

        md_files = sorted(cat_dir.glob("*.md"))
        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8")

            # Fix image paths: ../../images/ -> images/  (relative to project root)
            content = content.replace("../../images/", "images/")

            # Bump headings down one level so category header stays top-level
            # # -> ##, ## -> ###, etc.
            content = re.sub(r"^(#{1,5}) ", r"#\1 ", content, flags=re.MULTILINE)

            combined_parts.append(content.rstrip())
            combined_parts.append("\n\n---\n")

    combined_text = "\n".join(combined_parts)
    OUTPUT_MD.write_text(combined_text, encoding="utf-8")
    print(f"Combined markdown saved to: {OUTPUT_MD}")
    return OUTPUT_MD


def generate_pdf(md_path):
    """Convert combined markdown to PDF with base64-embedded images."""
    md_text = md_path.read_text(encoding="utf-8")

    # Replace markdown image references with base64 data URIs
    def image_to_base64(match):
        alt = match.group(1)
        rel_path = match.group(2)
        img_path = ROOT / rel_path
        if img_path.exists():
            data = base64.b64encode(img_path.read_bytes()).decode("utf-8")
            return f'<img src="data:image/png;base64,{data}" alt="{alt}">'
        else:
            return f"[Missing image: {rel_path}]"

    md_text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", image_to_base64, md_text)

    # Convert markdown -> HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists"],
    )

    # Wrap in styled HTML document
    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{
        size: letter;
        margin: 1.5cm;
    }}
    body {{
        font-family: Helvetica, Arial, sans-serif;
        line-height: 1.5;
        color: #222;
        font-size: 10pt;
    }}
    h1 {{
        color: #1a1a2e;
        border-bottom: 2px solid #1a1a2e;
        padding-bottom: 4px;
        margin-top: 30px;
        font-size: 20pt;
    }}
    h2 {{
        color: #16213e;
        margin-top: 24px;
        font-size: 15pt;
    }}
    h3 {{
        color: #0f3460;
        font-size: 12pt;
    }}
    h4 {{
        color: #333;
        font-size: 10pt;
    }}
    hr {{
        border: none;
        border-top: 1px solid #ccc;
        margin: 20px 0;
    }}
    img {{
        max-width: 100%;
        height: auto;
        margin: 8px 0;
    }}
    code {{
        background: #f0f0f0;
        padding: 1px 4px;
        font-size: 0.9em;
    }}
    pre {{
        background: #f0f0f0;
        padding: 10px;
        font-size: 0.85em;
    }}
    blockquote {{
        border-left: 3px solid #aaa;
        margin-left: 0;
        padding-left: 12px;
        color: #555;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 10px 0;
    }}
    th, td {{
        border: 1px solid #ccc;
        padding: 5px 8px;
        text-align: left;
    }}
    th {{
        background: #eee;
    }}
</style>
</head>
<body>
{html_body}
</body>
</html>"""

    with open(OUTPUT_PDF, "wb") as pdf_file:
        status = pisa.CreatePDF(html_doc, dest=pdf_file)

    if status.err:
        print(f"PDF generation had errors (code {status.err})")
    else:
        print(f"PDF saved to: {OUTPUT_PDF}")


if __name__ == "__main__":
    print("=== Step 1: Combining markdown files ===")
    md_path = combine_markdown_files()

    print("\n=== Step 2: Generating PDF ===")
    generate_pdf(md_path)
