#!/usr/bin/env python3
"""Export the manuscript's original figures for the static website.

Run with system Python (Pillow) and Poppler's pdftoppm installed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LANCZOS = getattr(Image, "Resampling", Image).LANCZOS
FIGURES = {
    "teaser": "teaser/lpg_drl_teaser.pdf",
    "framework": "framework_redesigned/lpg_drl_framework.pdf",
    "local-prior": "local_apf_guidance.pdf",
    "reward-design": "reward_redesigned/lpg_drl_reward_single_column.pdf",
    "training-reward": "reward_curve.pdf",
    "training-success": "success_rate_curve.pdf",
    "trajectory-offroad": "topdown_trajectory_comparison_off_road.pdf",
    "trajectory-flat": "topdown_trajectory_comparison_flat_land.pdf",
    "trajectory-obstacle-free": "topdown_trajectory_comparison_without_obstacle.pdf",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_dir", type=Path)
    args = parser.parse_args()
    output = ROOT / "assets/images"
    output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with tempfile.TemporaryDirectory(prefix="lpg-figures-") as temp:
        for name, relative in FIGURES.items():
            source = args.paper_dir / "images" / relative
            raster = Path(temp) / name
            subprocess.run([
                "pdftoppm", "-scale-to", "2800", "-singlefile", "-png",
                str(source), str(raster),
            ], check=True, capture_output=True)
            full = Image.open(raster.with_suffix(".png")).convert("RGB")
            full.save(output / f"{name}-full.webp", quality=94, method=6)
            preview = full.copy()
            preview.thumbnail((1600, 1600), LANCZOS)
            preview.save(output / f"{name}.webp", quality=90, method=6)
            manifest[name] = {
                "source": f"images/{relative}",
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "width": preview.width, "height": preview.height,
            }
            print(f"{name}: {preview.width} × {preview.height}")
    (output / "sources.json").write_text(json.dumps(manifest, indent=2) + "\n")

    # Social card uses the same manuscript teaser, without synthesizing scenery.
    card = Image.new("RGB", (1200, 630), "#f7faf9")
    draw = ImageDraw.Draw(card)
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    draw.text((48, 27), "LPG-DRL", fill="#13766c", font=ImageFont.truetype(font, 44))
    draw.text((49, 86), "Local priors. Attitude-aware off-road navigation.",
              fill="#263a37", font=ImageFont.truetype(font, 25))
    scene = Image.open(output / "teaser-full.webp")
    scene.thumbnail((1104, 480), LANCZOS)
    card.paste(scene, ((1200 - scene.width) // 2, 140))
    card.save(output / "social-preview.jpg", quality=90)


if __name__ == "__main__":
    main()
