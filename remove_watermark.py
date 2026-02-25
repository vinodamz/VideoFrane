"""
remove_watermark.py
────────────────────
Remove a watermark from one image or a whole folder of images.
Uses OpenCV inpainting to reconstruct the region under the watermark.

Modes
─────
  interactive   Open the image, draw a box around the watermark with your
                mouse → press ENTER/SPACE to confirm, ESC to cancel.
                (great for finding the right coordinates the first time)

  coords        Supply x,y,w,h directly — useful for batch processing
                when every image has the watermark in the same spot.

Usage
─────
  # Interactive — pick region on screen
  python remove_watermark.py <image_or_folder>

  # Supply coords  (x y width height measured from top-left corner)
  python remove_watermark.py <image_or_folder> --coords 10 850 200 40

  # Control inpainting strength (default 5 px)
  python remove_watermark.py <image_or_folder> --coords 10 850 200 40 --radius 10

  # Choose algorithm: telea (default) or ns
  python remove_watermark.py <image_or_folder> --coords 10 850 200 40 --algo ns

  # Save to a different folder
  python remove_watermark.py frames --coords 10 850 200 40 --out cleaned
"""

import os
import sys
import argparse
import cv2
import numpy as np


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Remove watermark from image(s) via inpainting.")
    p.add_argument("input", help="Image file or folder of images")
    p.add_argument("--coords", nargs=4, type=int, metavar=("X", "Y", "W", "H"),
                   help="Watermark region: X Y Width Height (pixels from top-left)")
    p.add_argument("--radius", type=int, default=5,
                   help="Inpainting neighbourhood radius in pixels (default: 5)")
    p.add_argument("--algo", choices=["telea", "ns"], default="telea",
                   help="Inpainting algorithm: telea (default, fast) or ns (Navier-Stokes)")
    p.add_argument("--out", default="cleaned",
                   help="Output folder when processing a batch (default: cleaned)")
    return p.parse_args()


# ── Helpers ───────────────────────────────────────────────────────────────────
SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}


def is_image(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in SUPPORTED


def collect_images(input_path: str) -> list[str]:
    if os.path.isfile(input_path):
        return [input_path]
    if os.path.isdir(input_path):
        return sorted(
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if is_image(os.path.join(input_path, f))
        )
    print(f"[ERROR] Not a file or directory: {input_path}")
    sys.exit(1)


def select_roi_interactive(image_path: str) -> tuple[int, int, int, int] | None:
    """Open image in a window; user draws a rectangle. Returns (x,y,w,h) or None."""
    img = cv2.imread(image_path)
    if img is None:
        print(f"[ERROR] Could not open image: {image_path}")
        return None

    print("\n  ┌─ HOW TO SELECT THE WATERMARK REGION ────────────────────────")
    print("  │  1. A window will open with the image.")
    print("  │  2. Click and drag to draw a box over the watermark.")
    print("  │  3. Press ENTER or SPACE to confirm, or ESC to cancel.")
    print("  └──────────────────────────────────────────────────────────────\n")

    roi = cv2.selectROI("Select watermark region — press ENTER to confirm, ESC to cancel",
                        img, showCrosshair=True, fromCenter=False)
    cv2.destroyAllWindows()

    x, y, w, h = roi
    if w == 0 or h == 0:
        print("  [INFO] No region selected — cancelled.")
        return None

    print(f"  Selected region → x={x}, y={y}, w={w}, h={h}")
    print(f"  TIP: Reuse with --coords {x} {y} {w} {h} for batch processing.\n")
    return x, y, w, h


def build_mask(image: np.ndarray, x: int, y: int, w: int, h: int,
               padding: int = 2) -> np.ndarray:
    """Create a binary mask with the watermark rectangle set to 255."""
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(image.shape[1], x + w + padding)
    y2 = min(image.shape[0], y + h + padding)
    mask[y1:y2, x1:x2] = 255
    return mask


def inpaint(image: np.ndarray, mask: np.ndarray,
            radius: int, algo: str) -> np.ndarray:
    flag = cv2.INPAINT_TELEA if algo == "telea" else cv2.INPAINT_NS
    return cv2.inpaint(image, mask, radius, flag)


def output_path(src: str, input_root: str, out_dir: str) -> str:
    """Mirror the input filename into the output directory."""
    basename = os.path.basename(src)
    return os.path.join(out_dir, basename)


# ── Core processing ───────────────────────────────────────────────────────────
def process_images(files: list[str], coords: tuple | None,
                   radius: int, algo: str, out_dir: str, input_root: str):

    os.makedirs(out_dir, exist_ok=True)

    # Determine region ──────────────────────────────────────────────────────
    if coords:
        x, y, w, h = coords
    else:
        if not files:
            print("[ERROR] No images found.")
            sys.exit(1)
        result = select_roi_interactive(files[0])
        if result is None:
            sys.exit(0)
        x, y, w, h = result

    print(f"  Watermark region : x={x}, y={y}, w={w}, h={h}")
    print(f"  Inpaint algo     : {algo.upper()}, radius={radius}")
    print(f"  Output folder    : {os.path.abspath(out_dir)}")
    print(f"  Images to process: {len(files)}\n")

    ok, failed = 0, 0
    for i, path in enumerate(files, 1):
        print(f"  Processing {i:>5}/{len(files)} : {os.path.basename(path)}", end="\r")

        img = cv2.imread(path)
        if img is None:
            print(f"\n  [WARN] Cannot read: {path}")
            failed += 1
            continue

        # Clamp region to actual image dimensions
        ih, iw = img.shape[:2]
        rx, ry = min(x, iw), min(y, ih)
        rw, rh = min(w, iw - rx), min(h, ih - ry)

        mask = build_mask(img, rx, ry, rw, rh)
        result = inpaint(img, mask, radius, algo)

        dest = output_path(path, input_root, out_dir)
        cv2.imwrite(dest, result)
        ok += 1

    print(f"\n\n[DONE] Processed {ok} image(s)  |  Failed: {failed}")
    print(f"[DONE] Clean images saved to: {os.path.abspath(out_dir)}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    args = parse_args()

    files = collect_images(args.input)
    coords = tuple(args.coords) if args.coords else None

    print(f"\n{'='*55}")
    print(f"  Watermark Remover")
    print(f"  Mode : {'Batch (coords supplied)' if coords else 'Interactive (select region)'}")
    print(f"{'='*55}")

    process_images(
        files=files,
        coords=coords,
        radius=args.radius,
        algo=args.algo,
        out_dir=args.out,
        input_root=args.input,
    )
