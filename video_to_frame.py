
import os
import sys
import cv2

def read_video(video_path: str, output_dir: str = "frames", save_frames: bool = False):
    """
    Read a video file and optionally save its frames as images.

    Args:
        video_path   : Path to the input video file.
        output_dir   : Directory where extracted frames will be saved (if save_frames=True).
        save_frames  : If True, each frame is saved as a JPEG image.
    """
    if not os.path.isfile(video_path):
        print(f"[ERROR] Video file not found: {video_path}")
        sys.exit(1)

    # Open the video file
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"[ERROR] Could not open video file: {video_path}")
        sys.exit(1)

    # ── Video properties ────────────────────────────────────────────────────
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps          = cap.get(cv2.CAP_PROP_FPS)
    width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0

    print("=" * 50)
    print(f"  Video File   : {video_path}")
    print(f"  Resolution   : {width} x {height}")
    print(f"  FPS          : {fps:.2f}")
    print(f"  Total Frames : {total_frames}")
    print(f"  Duration     : {duration_sec:.2f} seconds")
    print("=" * 50)

    # ── Optional: create output directory ──────────────────────────────────
    if save_frames:
        os.makedirs(output_dir, exist_ok=True)
        print(f"  Saving frames to: {os.path.abspath(output_dir)}\n")

    # ── Frame reading loop ─────────────────────────────────────────────────
    frame_index = 0
    while True:
        ret, frame = cap.read()

        if not ret:
            # End of video or read error
            break

        print(f"  Reading frame {frame_index + 1:>6} / {total_frames}", end="\r")

        if save_frames:
            filename = os.path.join(output_dir, f"frame_{frame_index:06d}.jpg")
            cv2.imwrite(filename, frame)

        frame_index += 1

    cap.release()
    print(f"\n[DONE] Successfully read {frame_index} frames.")

    if save_frames:
        print(f"[DONE] Frames saved in: {os.path.abspath(output_dir)}")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Usage:
    #   python video_to_frame.py <video_path> [output_dir] [--save]
    #
    # Examples:
    #   python video_to_frame.py sample.mp4
    #   python video_to_frame.py sample.mp4 my_frames --save

    if len(sys.argv) < 2:
        print("Usage: python video_to_frame.py <video_path> [output_dir] [--save]")
        sys.exit(1)

    video_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 and not sys.argv[2].startswith("--") else "frames"
    save_frames = "--save" in sys.argv

    read_video(video_path, output_dir=output_dir, save_frames=save_frames)
