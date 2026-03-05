import sys
from pathlib import Path

# Allow use of src modules
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

import argparse
from src.video.downloader import download_from_json

DEFAULT_INPUT = PROJECT_ROOT / "config" / "video_sources.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw_videos"


def main():
    parser = argparse.ArgumentParser(
        description="Download videos using yt-dlp from a JSON list"
    )

    parser.add_argument(
        "-i",
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to input JSON file",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output directory",
    )

    parser.add_argument(
        "--cookies-browser",
        default="none",
        help="Browser for yt-dlp cookies (chrome, edge, firefox)",
    )

    args = parser.parse_args()

    download_from_json(
        input_path=args.input,
        output_dir=args.output,
        cookies_browser=args.cookies_browser,
    )


if __name__ == "__main__":
    main()
