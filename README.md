# VideoFrane

A Python pipeline for extracting frames from videos, deduplicating them, removing watermarks, and converting the results into a PowerPoint presentation.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Pipeline

Run the stages in order:

```bash
# 1. Extract frames from a video file
python video_to_frame.py <video_path> [output_dir] [--save]

# 2. Remove near-duplicate frames in-place
python deduplicate_frames.py [frames_dir]              # default: frames/
python deduplicate_frames.py frames --threshold 8      # looser similarity (default: 5)
python deduplicate_frames.py frames --dry-run          # preview without deleting

# 3. Remove watermark — interactive or batch
python remove_watermark.py <image_or_folder>                            # interactive (draw box)
python remove_watermark.py frames --coords 10 850 200 40 --out cleaned  # batch with known coords
python remove_watermark.py frames --coords 10 850 200 40 --algo ns      # Navier-Stokes algorithm

# 4. Convert images to a PowerPoint presentation
python frames_to_ppt.py [folder] [output.pptx]
python frames_to_ppt.py cleaned output.pptx --title "My Video" --captions
python frames_to_ppt.py cleaned output.pptx --bg-color 1a1a2e
```

## Typical Workflow

```
video_to_frame.py  →  frames/
deduplicate_frames.py frames
remove_watermark.py frames --coords X Y W H --out cleaned
frames_to_ppt.py cleaned output.pptx
```

## Scripts

| Script | Purpose |
|--------|---------|
| `video_to_frame.py` | Extract frames from video using OpenCV |
| `deduplicate_frames.py` | Remove near-duplicate frames using perceptual hashing |
| `remove_watermark.py` | Remove watermark via OpenCV inpainting (interactive or batch) |
| `frames_to_ppt.py` | Convert image folder to 16:9 PowerPoint presentation |
