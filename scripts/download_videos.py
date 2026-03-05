import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "config" / "video_sources.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw_videos"


def load_input(json_path):
    """
    Parse input JSON with the structure:
    {"videos": ["", ""]}
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Input JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    videos = payload.get("videos") if isinstance(payload, dict) else None
    if not isinstance(videos, list):
        raise ValueError("Input JSON must contain a 'videos' list")

    links = [v.strip() for v in videos if isinstance(v, str) and v.strip()]
    if not links:
        raise ValueError("No valid video links found in input JSON")

    return links


def extract_video_id(video_link):
    """
    Extract a YouTube video ID from common URL formats.
    Returns None when the ID cannot be determined.
    """
    try:
        parsed = urlparse(video_link)
    except Exception:
        return None

    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    # https://www.youtube.com/watch?v=<id>
    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]

        # https://www.youtube.com/shorts/<id> or /embed/<id>
        parts = path.split("/")
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1]

    # https://youtu.be/<id>
    if "youtu.be" in host and path:
        return path.split("/")[0]

    return None


def already_downloaded(video_link, output_dir):
    """
    Check whether a file for this video ID already exists in output_dir.
    """
    video_id = extract_video_id(video_link)
    if not video_id:
        return False

    safe_id = re.escape(video_id)
    pattern = re.compile(rf".*\[{safe_id}\]\.[^.]+$")
    for file_path in Path(output_dir).glob("*"):
        if file_path.is_file() and pattern.match(file_path.name):
            return True
    return False


def download_video(video_link, output_dir, cookies_browser="none"):
    """
    Use yt-dlp to download a single video link.
    Returns True on success, False on failure.
    """
    output_template = str(Path(output_dir) / "%(title)s [%(id)s].%(ext)s")

    base_cmd = [
        "yt-dlp",
        "--no-playlist",
        "-o",
        output_template,
    ]

    if cookies_browser and cookies_browser.lower() != "none":
        base_cmd.extend(["--cookies-from-browser", cookies_browser])

    cmd = [*base_cmd, video_link]
    result = subprocess.run(cmd, check=False)
    return result.returncode == 0


def main(input_path, output_path, cookies_browser):
    """
    Load input JSON and download each video, printing successes.
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    links = load_input(input_path)

    successes = 0
    failures = 0
    skipped = 0
    total = len(links)

    for idx, link in enumerate(links, start=1):
        print(f"[{idx}/{total}] Downloading: {link}")
        if already_downloaded(link, output_dir):
            skipped += 1
            print("  -> Skipped (already in output)")
            continue

        ok = download_video(link, output_dir, cookies_browser=cookies_browser)
        if ok:
            successes += 1
            print("  -> Success")
        else:
            failures += 1
            print("  -> Failed")

    print(
        f"Finished. Successes: {successes}, Skipped: {skipped}, "
        f"Failures: {failures}, Total: {total}"
    )
    if failures:
        print("Hint: try updating yt-dlp (`yt-dlp -U`) and rerun.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download videos using yt-dlp from a JSON list"
    )
    parser.add_argument(
        "-i",
        "--input",
        default=str(DEFAULT_INPUT),
        help="Path to input JSON file (expects {'videos': [...]})",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output directory for downloaded videos",
    )
    parser.add_argument(
        "--cookies-browser",
        default="none",
        help="Browser for yt-dlp cookies (e.g., chrome, edge, firefox), or 'none'",
    )

    args = parser.parse_args()
    main(args.input, args.output, args.cookies_browser)
