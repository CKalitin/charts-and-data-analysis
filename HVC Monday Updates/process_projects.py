"""
Project-level pipeline for Monday.com update exports.

This script keeps projects separated by output folder while reusing the same
HTML -> markdown extraction and markdown -> PDF rendering logic.

Usage:
  python process_projects.py --list
  python process_projects.py --project slaveboard
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List

from extract_updates import extract_updates
from combine_and_pdf import generate_pdf


ROOT = Path(__file__).parent
IMAGES_DIR = ROOT / "images"
OUTPUT_DIR = ROOT / "output"
DEFAULT_PROJECT = "slaveboard"


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    source_files: List[Path]
    output_subdir: str
    output_basename: str


PROJECTS = {
    "slaveboard": ProjectConfig(
        name="slaveboard",
        source_files=[ROOT / "html" / "BMS Projects - Slaveboard rev 2.0.htm"],
        output_subdir="slaveboard",
        output_basename="slaveboard",
    ),
}


def ensure_files_exist(paths: List[Path], project_name: str) -> None:
    missing = [path for path in paths if not path.exists()]
    if not missing:
        return

    missing_list = "\n".join(f"  - {path}" for path in missing)
    raise FileNotFoundError(
        f"Missing source files for project '{project_name}':\n{missing_list}"
    )


def extract_project_sources(config: ProjectConfig, extracted_dir: Path) -> List[Path]:
    extracted_dir.mkdir(parents=True, exist_ok=True)

    md_files = []
    for index, source_file in enumerate(config.source_files, start=1):
        part_name = f"{index:02d} - {source_file.stem}_Updates.md"
        output_md = extracted_dir / part_name

        print("=" * 60)
        print(f"Extracting: {source_file}")
        print(f"Output:     {output_md}")
        print("=" * 60)

        # output/<project>/extracted -> ../../images
        extract_updates(
            str(source_file),
            str(output_md),
            str(IMAGES_DIR),
            "../../images",
        )

        md_files.append(output_md)

    return md_files


def combine_project_markdown(md_files: List[Path], output_md: Path) -> None:
    parts = []
    for md_file in sorted(md_files):
        content = md_file.read_text(encoding="utf-8").strip()
        if content:
            parts.append(content)

    output_md.parent.mkdir(parents=True, exist_ok=True)
    combined = "\n\n---\n\n".join(parts).rstrip() + "\n"
    output_md.write_text(combined, encoding="utf-8")
    print(f"Combined markdown saved to: {output_md}")


def run_project(project_name: str) -> tuple[Path, Path]:
    if project_name not in PROJECTS:
        valid = ", ".join(sorted(PROJECTS.keys()))
        raise ValueError(f"Unknown project '{project_name}'. Valid options: {valid}")

    config = PROJECTS[project_name]
    ensure_files_exist(config.source_files, config.name)

    project_output_dir = OUTPUT_DIR / config.output_subdir
    extracted_dir = project_output_dir / "extracted"
    output_md = project_output_dir / f"{config.output_basename}.md"
    output_pdf = project_output_dir / f"{config.output_basename}.pdf"

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    md_files = extract_project_sources(config, extracted_dir)
    combine_project_markdown(md_files, output_md)

    print("\nGenerating PDF...")
    generate_pdf(output_md, output_pdf)

    return output_md, output_pdf


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process project update exports")
    parser.add_argument(
        "--project",
        choices=sorted(PROJECTS.keys()),
        default=DEFAULT_PROJECT,
        help=f"Project key to process (default: {DEFAULT_PROJECT})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available project keys",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.list:
        print("Available projects:")
        for project_name in sorted(PROJECTS.keys()):
            print(f"  - {project_name}")
        return

    output_md, output_pdf = run_project(args.project)
    print("\nDone.")
    print(f"Markdown: {output_md}")
    print(f"PDF:      {output_pdf}")


if __name__ == "__main__":
    main()
