import argparse
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = PROJECT_ROOT / "config" / "video_sources.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw_videos"
COOKIE_BROWSER_CANDIDATES = ("chrome", "edge", "firefox", "brave")


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


def download_video(video_link, output_dir, cookies_browser="auto"):
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

    attempts = [("without cookies", [])]
    if cookies_browser == "auto":
        attempts.extend(
            (f"with {browser} cookies", ["--cookies-from-browser", browser])
            for browser in COOKIE_BROWSER_CANDIDATES
        )
    elif cookies_browser and cookies_browser.lower() != "none":
        attempts.append(
            (f"with {cookies_browser} cookies", ["--cookies-from-browser", cookies_browser])
        )

    for attempt_label, extra_args in attempts:
        print(f"  -> Attempt: {attempt_label}")
        cmd = [*base_cmd, *extra_args, video_link]
        result = subprocess.run(cmd, check=False)
        if result.returncode == 0:
            return True

    return False


def main(input_path, output_path, cookies_browser):
    """
    Load input JSON and download each video, printing successes.
    """
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    links = load_input(input_path)

    successes = 0
    failures = 0
    total = len(links)

    for idx, link in enumerate(links, start=1):
        print(f"[{idx}/{total}] Downloading: {link}")
        ok = download_video(link, output_dir, cookies_browser=cookies_browser)
        if ok:
            successes += 1
            print("  -> Success")
        else:
            failures += 1
            print("  -> Failed")

    print(f"Finished. Successes: {successes}, Failures: {failures}, Total: {total}")
    if failures:
        print(
            "Hint: if videos fail with bot/sign-in checks, log in to YouTube in a browser and run with "
            "--cookies-browser chrome|edge|firefox (or use default auto)."
        )


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
        default="auto",
        help="Browser for yt-dlp cookies (e.g., chrome, edge, firefox), 'auto' to try common browsers, or 'none'",
    )

    args = parser.parse_args()
    main(args.input, args.output, args.cookies_browser)
