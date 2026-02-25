"""
deduplicate_frames.py
─────────────────────
Reads JPEG frames from a folder, compares them using perceptual hashing,
and removes near-duplicate images — keeping only visually distinct frames.

Usage:
    python deduplicate_frames.py [frames_dir] [--threshold N] [--dry-run]

Arguments:
    frames_dir       : Folder containing JPEG frames  (default: "frames")
    --threshold N    : Max hash distance to consider two images "same"
                       0 = exact duplicates only, 10 = very similar (default: 5)
    --dry-run        : Print what would be deleted without actually deleting

Examples:
    python deduplicate_frames.py
    python deduplicate_frames.py frames --threshold 8
    python deduplicate_frames.py frames --threshold 5 --dry-run
"""

import os
import sys
import argparse
from PIL import Image
import imagehash


def parse_args():
    parser = argparse.ArgumentParser(description="Remove duplicate/similar JPEG frames.")
    parser.add_argument("frames_dir", nargs="?", default="frames",
                        help="Directory containing JPEG frames (default: frames)")
    parser.add_argument("--threshold", type=int, default=5,
                        help="Max perceptual hash distance to treat as duplicate (default: 5)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be deleted without deleting")
    return parser.parse_args()


def load_jpeg_files(folder: str) -> list[str]:
    """Return sorted list of JPEG file paths in the given folder."""
    supported = {".jpg", ".jpeg"}
    files = [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if os.path.splitext(f)[1].lower() in supported
    ]
    return files


def compute_hashes(file_paths: list[str]) -> list[tuple[str, object]]:
    """Compute perceptual hash for each image file."""
    results = []
    total = len(file_paths)
    for i, path in enumerate(file_paths, 1):
        print(f"  Hashing {i:>6}/{total} : {os.path.basename(path)}", end="\r")
        try:
            img = Image.open(path)
            h = imagehash.phash(img)   # perceptual hash (8×8 DCT)
            results.append((path, h))
        except Exception as e:
            print(f"\n  [WARN] Could not read {path}: {e}")
    print()  # newline after progress
    return results


def find_duplicates(hashed: list[tuple[str, object]], threshold: int) -> set[str]:
    """
    Compare consecutive frames.  If two adjacent frames are within
    `threshold` hash distance, the later one is a duplicate.
    Returns the set of file paths to DELETE.
    """
    to_delete: set[str] = set()
    kept_path, kept_hash = hashed[0]

    for path, h in hashed[1:]:
        distance = kept_hash - h
        if distance <= threshold:
            # Too similar → mark for deletion
            to_delete.add(path)
        else:
            # Different enough → this becomes the new reference
            kept_path, kept_hash = path, h

    return to_delete


def main():
    args = parse_args()
    folder = args.frames_dir
    threshold = args.threshold
    dry_run = args.dry_run

    # ── Validate folder ───────────────────────────────────────────────────
    if not os.path.isdir(folder):
        print(f"[ERROR] Directory not found: {folder}")
        sys.exit(1)

    # ── Load files ────────────────────────────────────────────────────────
    files = load_jpeg_files(folder)
    if not files:
        print(f"[ERROR] No JPEG files found in: {folder}")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  Frames directory : {os.path.abspath(folder)}")
    print(f"  Total JPEGs found: {len(files)}")
    print(f"  Similarity thresh: {threshold}  (hash distance ≤ {threshold} → duplicate)")
    print(f"  Mode             : {'DRY RUN (no files deleted)' if dry_run else 'LIVE (will delete duplicates)'}")
    print(f"{'='*55}\n")

    # ── Compute hashes ────────────────────────────────────────────────────
    print("[1/3] Computing perceptual hashes …")
    hashed = compute_hashes(files)

    # ── Find duplicates ───────────────────────────────────────────────────
    print("[2/3] Detecting duplicates …")
    to_delete = find_duplicates(hashed, threshold)

    kept = len(files) - len(to_delete)
    print(f"\n  Unique frames to keep : {kept}")
    print(f"  Duplicate frames found: {len(to_delete)}")

    # ── Delete or report ──────────────────────────────────────────────────
    print("\n[3/3] Removing duplicates …")
    if dry_run:
        for path in sorted(to_delete):
            print(f"  [DRY-RUN] Would delete: {os.path.basename(path)}")
        print(f"\n[DONE] Dry run complete. {len(to_delete)} files would be removed.")
    else:
        deleted = 0
        for path in sorted(to_delete):
            try:
                os.remove(path)
                deleted += 1
            except Exception as e:
                print(f"  [WARN] Could not delete {path}: {e}")

        print(f"\n[DONE] Removed {deleted} duplicate frames.")
        print(f"[DONE] {kept} unique frames remain in: {os.path.abspath(folder)}")


if __name__ == "__main__":
    main()
