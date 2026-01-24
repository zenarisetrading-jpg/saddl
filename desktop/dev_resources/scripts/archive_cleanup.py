#!/usr/bin/env python3
"""
Archive Cleanup Script for Saddle Desktop
==========================================
Moves redundant/backup files to a timestamped archive folder.
Run with --dry-run first to preview changes.

Usage:
    python archive_cleanup.py --dry-run   # Preview only
    python archive_cleanup.py             # Execute archive
"""

import os
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Base directory
DESKTOP_DIR = Path(__file__).parent.resolve()
ARCHIVE_DIR = DESKTOP_DIR / f"_archived_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# =============================================================================
# FILES TO ARCHIVE (Verified redundant/backup files)
# =============================================================================

FILES_TO_ARCHIVE = [
    # Root level - deprecated/old entry points
    "ppcsuite.py",                    # Old entry point (refs non-existent ai_insights)
    "ppcsuite_v4_deprecated.py",      # Explicitly deprecated
    
    # Root level - debug/one-time scripts
    "debug_org_accounts.py",
    "fix_org_accounts.py",
    "import os.py",                   # Incomplete/accidental file
    
    # Root level - migration utilities (one-time use)
    "apply_postgres_migration.py",
    "migrate_bid_types.py",
    "postgres_migration.sql",
    "run_login_test.py",
    "run_migration_step1.py",
    "run_migration_step3.py",
    "run_migration_step_3_5.py",
    "run_seed_step2.py",
    "verify_login_render.py",
    
    # Root level - test/sample data files
    "Bulk-SP.xlsx",
    "dec1-19.xlsx",
    "Sponsored_Products_Advertised_product_report.xlsx",
    "ppc_test.db",
    "Archive.zip",
    
    # Features - backup files
    "features/impact_dashboard_backup.py",
    "features/impact_dashboard_backup_jan2.py",
    
    # Landing - backup files
    "landing/index.html.backup",
    "landing/index_old_backup.html",
    "landing/styles_old_backup.css",
    
    # Orchestration - superseded files (NOT PRD.md - that's orchestration-specific)
    "orchestration/claude_code_orchestrator_fixed.py",
    "orchestration/start.sh",         # Superseded by start_fixed.sh
]

# =============================================================================
# DIRECTORIES TO ARCHIVE
# =============================================================================

DIRS_TO_ARCHIVE = [
    "landing_backup_1768048542",      # Complete duplicate of landing
    "backups",                        # Backup folder
    "Redesign/backup",                # Old landing backups
]

# =============================================================================
# CONTENTIOUS FILES - need review, renamed with _REVIEW suffix
# =============================================================================

CONTENTIOUS_FILES = [
    # These will be moved but marked for review
    ("orchestration/claude_code_prompts.txt", "claude_code_prompts_REVIEW.txt"),
]


def archive_file(src: Path, dry_run: bool) -> bool:
    """Move a single file to archive."""
    if not src.exists():
        print(f"  ⚠️  SKIP (not found): {src.relative_to(DESKTOP_DIR)}")
        return False
    
    # Create relative path in archive
    rel_path = src.relative_to(DESKTOP_DIR)
    dest = ARCHIVE_DIR / rel_path
    
    if dry_run:
        print(f"  📦 WOULD MOVE: {rel_path}")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"  ✅ MOVED: {rel_path}")
    return True


def archive_directory(src: Path, dry_run: bool) -> bool:
    """Move an entire directory to archive."""
    if not src.exists():
        print(f"  ⚠️  SKIP (not found): {src.relative_to(DESKTOP_DIR)}")
        return False
    
    rel_path = src.relative_to(DESKTOP_DIR)
    dest = ARCHIVE_DIR / rel_path
    
    if dry_run:
        file_count = sum(1 for _ in src.rglob("*") if _.is_file())
        print(f"  📁 WOULD MOVE DIR: {rel_path}/ ({file_count} files)")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"  ✅ MOVED DIR: {rel_path}/")
    return True


def archive_contentious(src: Path, new_name: str, dry_run: bool) -> bool:
    """Move contentious file with renamed suffix for review."""
    if not src.exists():
        print(f"  ⚠️  SKIP (not found): {src.relative_to(DESKTOP_DIR)}")
        return False
    
    rel_path = src.relative_to(DESKTOP_DIR)
    dest = ARCHIVE_DIR / rel_path.parent / new_name
    
    if dry_run:
        print(f"  🔍 WOULD MOVE (for review): {rel_path} → {new_name}")
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        print(f"  🔍 MOVED (review): {rel_path} → {new_name}")
    return True


def write_manifest(archived_items: list, dry_run: bool):
    """Write manifest of archived files."""
    if dry_run:
        return
    
    manifest_path = ARCHIVE_DIR / "MANIFEST.md"
    with open(manifest_path, "w") as f:
        f.write(f"# Archive Manifest\n")
        f.write(f"Created: {datetime.now().isoformat()}\n\n")
        f.write(f"## Archived Items ({len(archived_items)} total)\n\n")
        for item in archived_items:
            f.write(f"- {item}\n")
        f.write(f"\n---\n")
        f.write(f"To restore, move items back to `desktop/` directory.\n")
    print(f"\n📝 Manifest written to: {manifest_path.relative_to(DESKTOP_DIR)}")


def main():
    parser = argparse.ArgumentParser(description="Archive redundant files from desktop project")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    args = parser.parse_args()
    
    dry_run = args.dry_run
    archived_items = []
    
    print("=" * 60)
    print("🗂️  SADDLE DESKTOP ARCHIVE CLEANUP")
    print("=" * 60)
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be moved\n")
    else:
        print(f"📦 Archive directory: {ARCHIVE_DIR.name}/\n")
        ARCHIVE_DIR.mkdir(exist_ok=True)
    
    # Archive individual files
    print("📄 FILES:")
    for file_path in FILES_TO_ARCHIVE:
        src = DESKTOP_DIR / file_path
        if archive_file(src, dry_run):
            archived_items.append(file_path)
    
    # Archive directories
    print("\n📁 DIRECTORIES:")
    for dir_path in DIRS_TO_ARCHIVE:
        src = DESKTOP_DIR / dir_path
        if archive_directory(src, dry_run):
            archived_items.append(f"{dir_path}/")
    
    # Archive contentious files with rename
    if CONTENTIOUS_FILES:
        print("\n🔍 CONTENTIOUS (renamed for review):")
        for file_path, new_name in CONTENTIOUS_FILES:
            src = DESKTOP_DIR / file_path
            if archive_contentious(src, new_name, dry_run):
                archived_items.append(f"{file_path} → {new_name}")
    
    # Write manifest
    if not dry_run:
        write_manifest(archived_items, dry_run)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: {len(archived_items)} items {'would be' if dry_run else ''} archived")
    if dry_run:
        print("\n💡 Run without --dry-run to execute the archive.")
    print("=" * 60)


if __name__ == "__main__":
    main()
