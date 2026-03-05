import json
import re
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse


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

    if "youtube.com" in host:
        qs = parse_qs(parsed.query)
        if "v" in qs and qs["v"]:
            return qs["v"][0]

        parts = path.split("/")
        if len(parts) >= 2 and parts[0] in {"shorts", "embed", "live"}:
            return parts[1]

    if "youtu.be" in host and path:
        return path.split("/")[0]

    return None


def already_downloaded(video_link, output_dir):
    """
    Check whether a file for this video ID already exists.
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
    Download a single video with yt-dlp.
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


def download_from_json(input_path, output_dir, cookies_browser="none"):
    """
    Batch download from JSON list.
    """
    output_dir = Path(output_dir)
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
            print("  -> Skipped (already exists)")
            continue

        ok = download_video(link, output_dir, cookies_browser)

        if ok:
            successes += 1
            print("  -> Success")
        else:
            failures += 1
            print("  -> Failed")

    print(
        f"\nFinished. Successes: {successes}, "
        f"Skipped: {skipped}, Failures: {failures}, Total: {total}"
    )

    if failures:
        print("Hint: try updating yt-dlp (`yt-dlp -U`).")
