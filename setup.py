#!/usr/bin/env python3
"""
Setup script to create necessary directories and starter files for the LMS.

Usage:
  python setup.py
  python setup.py --force-placeholders   # recreate placeholder CSS/JS (won't overwrite unless forced)
"""

from __future__ import annotations

import argparse
from pathlib import Path

# Directories to create (relative to project root)
DIRECTORIES = [
    "static",
    "static/css",
    "static/js",
    "static/images",
    "uploads",
    "templates",
    "templates/auth",
    "templates/courses",
    "templates/dashboard",
    "templates/assignments",
    "routes",
]

# Placeholder contents (only used when file is missing, unless forced)
PLACEHOLDER_CSS = """/* Minimal starter styles for LMS (placeholder)
   NOTE: If you already have a real style.css, this file should not overwrite it.
*/

body {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}

.card {
  margin-bottom: 1.5rem;
}
"""

PLACEHOLDER_JS = """// Minimal starter JS for LMS (placeholder)
document.addEventListener("DOMContentLoaded", function () {
  // Auto-hide Bootstrap alerts after 5 seconds
  const alerts = document.querySelectorAll(".alert");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.classList.remove("show");
      setTimeout(() => alert.remove(), 150);
    }, 5000);
  });
});
"""


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_file_if_missing(path: Path, content: str) -> bool:
    """
    Returns True if file was created, False if it already existed.
    """
    if path.exists():
        return False
    path.write_text(content, encoding="utf-8")
    return True


def write_file_force(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def setup_directories(force_placeholders: bool = False) -> None:
    base_path = Path(__file__).resolve().parent

    print("Creating directory structure...\n")

    for rel_dir in DIRECTORIES:
        dir_path = base_path / rel_dir
        existed = dir_path.exists()
        ensure_dir(dir_path)
        if existed:
            print(f"⚠ Already exists: {rel_dir}/")
        else:
            print(f"✓ Created: {rel_dir}/")

    # routes/__init__.py
    routes_init = base_path / "routes" / "__init__.py"
    if write_file_if_missing(routes_init, "# Routes package\n"):
        print("✓ Created: routes/__init__.py")
    else:
        print("⚠ Already exists: routes/__init__.py")

    # uploads/.gitkeep (track empty uploads folder)
    gitkeep = base_path / "uploads" / ".gitkeep"
    if write_file_if_missing(gitkeep, ""):
        print("✓ Created: uploads/.gitkeep")
    else:
        print("⚠ Already exists: uploads/.gitkeep")

    # Placeholders (do NOT overwrite your real files unless forced)
    css_file = base_path / "static" / "css" / "style.css"
    js_file = base_path / "static" / "js" / "main.js"

    if force_placeholders:
        write_file_force(css_file, PLACEHOLDER_CSS)
        print("✓ Wrote: static/css/style.css (forced placeholder)")
        write_file_force(js_file, PLACEHOLDER_JS)
        print("✓ Wrote: static/js/main.js (forced placeholder)")
    else:
        if write_file_if_missing(css_file, PLACEHOLDER_CSS):
            print("✓ Created: static/css/style.css (placeholder)")
        else:
            print("⚠ Already exists: static/css/style.css (left unchanged)")

        if write_file_if_missing(js_file, PLACEHOLDER_JS):
            print("✓ Created: static/js/main.js (placeholder)")
        else:
            print("⚠ Already exists: static/js/main.js (left unchanged)")

    print("\n✅ Setup complete! Directory structure is ready.\n")
    print("Next steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Configure environment variables in .env")
    print("3. Run the application: python app.py")


def main() -> None:
    parser = argparse.ArgumentParser(description="Setup LMS directories and starter files.")
    parser.add_argument(
        "--force-placeholders",
        action="store_true",
        help="Overwrite placeholder CSS/JS even if they already exist.",
    )
    args = parser.parse_args()
    setup_directories(force_placeholders=args.force_placeholders)


if __name__ == "__main__":
    main()