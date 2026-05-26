"""
Download and transcribe Uma Musume strategy videos for research.

Goal: feed us evidence-based notes on how UG rank is achieved so the
career bot's preset profile + scoring engine can target it.

Usage examples
--------------
# Just probe metadata (no download), one or many URLs:
python scripts/transcribe_uma_guide.py probe https://www.youtube.com/watch?v=xxxx

# Download + transcribe one URL with the small model (CPU friendly):
python scripts/transcribe_uma_guide.py run https://www.youtube.com/watch?v=xxxx \
    --model small --language ja

# Transcribe an already-downloaded file:
python scripts/transcribe_uma_guide.py local "G:/yt-dlp/Downloaded Videos/foo.mp4" \
    --model small --language ja

Outputs land under data/uma_guides/<video-id>/
  - meta.json       (title, uploader, chapters, lang, etc.)
  - audio.m4a       (extracted with ffmpeg, optional)
  - transcript.json (timestamped segments)
  - transcript.txt  (flat readable text)

This script is intentionally self-contained and does NOT depend on the
external mandarin/tools repo. It borrows the public faster-whisper +
yt-dlp recipes from there.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO = Path(__file__).resolve().parents[1]
OUT_ROOT = REPO / "data" / "uma_guides"

YT_DLP_CANDIDATES = (
    Path(r"G:\yt-dlp\yt-dlp.exe"),
    Path(r"G:\yt-dlp\yt-dlp_2.exe"),
)
COOKIES_FILE = Path(r"G:\yt-dlp\cookies.txt")


def find_yt_dlp() -> Path:
    for p in YT_DLP_CANDIDATES:
        if p.is_file():
            return p
    raise SystemExit("yt-dlp executable not found under G:\\yt-dlp\\")


def extract_video_id(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})", url)
    if not m:
        raise SystemExit(f"Could not parse a YouTube video id from {url!r}")
    return m.group(1)


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    """Thin wrapper that prints the command first then runs it."""
    print("+", " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        capture_output=capture,
        encoding="utf-8",
        errors="replace",
    )


def cookie_args() -> list[str]:
    """Prefer the on-disk cookies.txt; fall back to firefox if absent."""
    if COOKIES_FILE.is_file():
        return ["--cookies", str(COOKIES_FILE)]
    return ["--cookies-from-browser", "firefox"]


def probe(url: str) -> dict:
    yt = find_yt_dlp()
    cmd = [str(yt), "--no-warnings", "--skip-download", "--dump-single-json", url, *cookie_args()]
    proc = run(cmd, capture=True)
    data = json.loads(proc.stdout)
    summary = {
        "id": data.get("id"),
        "title": data.get("title"),
        "uploader": data.get("uploader") or data.get("channel"),
        "duration_s": data.get("duration"),
        "language": data.get("language"),
        "upload_date": data.get("upload_date"),
        "webpage_url": data.get("webpage_url") or url,
        "view_count": data.get("view_count"),
        "chapters": [
            {
                "start": c.get("start_time"),
                "end": c.get("end_time"),
                "title": c.get("title"),
            }
            for c in (data.get("chapters") or [])
        ],
        "description": (data.get("description") or "").strip(),
    }
    return summary


def output_dir(video_id: str) -> Path:
    d = OUT_ROOT / video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_meta(meta: dict, out_dir: Path) -> Path:
    path = out_dir / "meta.json"
    path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def download_audio(url: str, video_id: str, out_dir: Path) -> Path:
    yt = find_yt_dlp()
    audio_template = str(out_dir / f"{video_id}.%(ext)s")
    cmd = [
        str(yt),
        "--no-warnings",
        "-o", audio_template,
        "-f", "bestaudio/best",
        "-x",
        "--audio-format", "m4a",
        url,
        *cookie_args(),
    ]
    run(cmd)
    for ext in (".m4a", ".webm", ".mp3", ".opus"):
        p = out_dir / f"{video_id}{ext}"
        if p.is_file():
            return p
    raise SystemExit("Audio file not found after yt-dlp download.")


def pick_device() -> tuple[str, str]:
    try:
        import torch

        if torch.cuda.is_available():
            return "cuda", "float16"
    except ImportError:
        pass
    return "cpu", "int8"


def load_whisper(model_size: str):
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise SystemExit(
            "faster-whisper is not installed. Run: pip install faster-whisper"
        ) from e
    device, compute = pick_device()
    print(f"Loading Whisper '{model_size}' on {device} ({compute})...", flush=True)
    kw: dict = {"device": device, "compute_type": compute}
    if device == "cpu":
        kw["cpu_threads"] = max(1, (subprocess.os.cpu_count() or 4) - 1)
    return WhisperModel(model_size, **kw)


def transcribe(audio_path: Path, *, model_size: str, language: str | None) -> tuple[list[dict], dict]:
    model = load_whisper(model_size)
    kwargs: dict = {
        "beam_size": 1,
        "vad_filter": True,
        "word_timestamps": False,
        "condition_on_previous_text": False,
        "no_speech_threshold": 0.6,
        "initial_prompt": (
            "Uma Musume Pretty Derby training guide. Mentions UG / UG+ / SS / SS+ rank, "
            "Trailblazer / Make a New Track scenario, rank_score, stats speed stamina power "
            "guts wit, skill points, racing strategy."
        ),
    }
    if language:
        kwargs["language"] = language

    print(f"Transcribing {audio_path.name} (model={model_size}, lang={language or 'auto'})", flush=True)
    t0 = time.perf_counter()
    seg_iter, info = model.transcribe(str(audio_path), **kwargs)

    segments: list[dict] = []
    for i, seg in enumerate(seg_iter):
        text = (seg.text or "").strip()
        if not text:
            continue
        segments.append(
            {
                "id": i,
                "start": round(float(seg.start), 2),
                "end": round(float(seg.end), 2),
                "text": text,
            }
        )
        if i % 25 == 0 and i:
            print(f"  ...{i} segments ({seg.end:.0f}s)", flush=True)

    elapsed = time.perf_counter() - t0
    info_dict = {
        "language": getattr(info, "language", None),
        "language_probability": round(float(getattr(info, "language_probability", 0) or 0), 4),
        "duration": round(float(getattr(info, "duration", 0) or 0), 2),
        "transcribe_seconds": round(elapsed, 1),
        "model": model_size,
    }
    print(
        f"Done: {len(segments)} segments, "
        f"lang={info_dict['language']} "
        f"({info_dict['language_probability']:.0%}), "
        f"{info_dict['transcribe_seconds']:.0f}s wall"
    )
    return segments, info_dict


def write_transcript(out_dir: Path, segments: list[dict], info_dict: dict, meta: dict) -> tuple[Path, Path]:
    json_path = out_dir / "transcript.json"
    json_path.write_text(
        json.dumps(
            {
                "video_id": meta.get("id"),
                "title": meta.get("title"),
                "info": info_dict,
                "segments": segments,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    flat = out_dir / "transcript.txt"
    with flat.open("w", encoding="utf-8") as fh:
        for seg in segments:
            ts = time.strftime("%H:%M:%S", time.gmtime(seg["start"]))
            fh.write(f"[{ts}] {seg['text']}\n")
    return json_path, flat


def cmd_probe(args: argparse.Namespace) -> None:
    for url in args.urls:
        print(f"==== {url} ====")
        m = probe(url)
        print(json.dumps(m, ensure_ascii=False, indent=2))


def cmd_run(args: argparse.Namespace) -> None:
    for url in args.urls:
        vid = extract_video_id(url)
        out_dir = output_dir(vid)
        print(f"=== {url}  ->  {out_dir} ===")
        meta = probe(url)
        write_meta(meta, out_dir)
        audio = download_audio(url, vid, out_dir)
        segments, info_dict = transcribe(audio, model_size=args.model, language=args.language)
        write_transcript(out_dir, segments, info_dict, meta)
        print(f"OK {vid}")


def vtt_to_segments(vtt_text: str) -> list[dict]:
    """Parse a WebVTT auto-caption file into [{start,end,text}] segments.
    Deduplicates rolling-window captions (YouTube auto-CC repeats each line)."""
    segments: list[dict] = []
    seen_text: set[str] = set()
    block_re = re.compile(
        r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})[^\n]*\n(.+?)(?=\n\n|\Z)",
        re.S,
    )
    for m in block_re.finditer(vtt_text):
        h1, mi1, s1, ms1, h2, mi2, s2, ms2, body = m.groups()
        start = int(h1) * 3600 + int(mi1) * 60 + int(s1) + int(ms1) / 1000
        end = int(h2) * 3600 + int(mi2) * 60 + int(s2) + int(ms2) / 1000
        text = re.sub(r"<[^>]+>", "", body)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or text in seen_text:
            continue
        seen_text.add(text)
        segments.append({"id": len(segments), "start": round(start, 2), "end": round(end, 2), "text": text})
    return segments


def fetch_auto_captions(url: str, out_dir: Path, lang: str = "en") -> Path | None:
    """Download YouTube auto-captions (much faster than transcribing).

    Returns the local .vtt path or None if no captions were found.
    """
    yt = find_yt_dlp()
    template = str(out_dir / "cc.%(ext)s")
    cmd = [
        str(yt),
        "--no-warnings",
        "--skip-download",
        "--write-auto-subs",
        "--sub-lang", f"{lang},{lang}-orig",
        "--sub-format", "vtt",
        "--convert-subs", "vtt",
        "-o", template,
        url,
        *cookie_args(),
    ]
    run(cmd)
    candidates = sorted(out_dir.glob("cc*.vtt"))
    if not candidates:
        return None
    return candidates[0]


def cmd_captions(args: argparse.Namespace) -> None:
    """Pull auto-captions for one or more URLs and emit transcript.{json,txt}."""
    for url in args.urls:
        vid = extract_video_id(url)
        out_dir = output_dir(vid)
        print(f"=== {url}  ->  {out_dir} ===")
        meta = probe(url)
        write_meta(meta, out_dir)
        vtt = fetch_auto_captions(url, out_dir, lang=args.language or "en")
        if not vtt:
            print(f"!! No captions for {vid}; consider `run` (Whisper) instead.")
            continue
        segments = vtt_to_segments(vtt.read_text(encoding="utf-8"))
        info = {"language": args.language or "en", "source": "youtube-auto-cc", "vtt_file": vtt.name}
        write_transcript(out_dir, segments, info, meta)
        print(f"OK {vid}: {len(segments)} caption segments")


def cmd_local(args: argparse.Namespace) -> None:
    audio = Path(args.path)
    if not audio.is_file():
        raise SystemExit(f"File not found: {audio}")
    vid = args.video_id or audio.stem
    out_dir = output_dir(vid)
    meta = {"id": vid, "title": audio.stem, "source": "local-file"}
    write_meta(meta, out_dir)
    segments, info_dict = transcribe(audio, model_size=args.model, language=args.language)
    write_transcript(out_dir, segments, info_dict, meta)
    print(f"OK {vid}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("probe", help="Dump YouTube metadata without downloading")
    p.add_argument("urls", nargs="+")
    p.set_defaults(func=cmd_probe)

    p = sub.add_parser("run", help="Download audio + transcribe one or more URLs")
    p.add_argument("urls", nargs="+")
    p.add_argument("--model", default="small", help="faster-whisper model (tiny/base/small/medium/large-v3)")
    p.add_argument("--language", default=None, help="ISO code (e.g. ja, en); default auto")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser(
        "captions",
        help="Pull YouTube auto-captions (fast, no Whisper)",
    )
    p.add_argument("urls", nargs="+")
    p.add_argument("--language", default="en")
    p.set_defaults(func=cmd_captions)

    p = sub.add_parser("local", help="Transcribe a local audio/video file")
    p.add_argument("path")
    p.add_argument("--video-id", default=None)
    p.add_argument("--model", default="small")
    p.add_argument("--language", default=None)
    p.set_defaults(func=cmd_local)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
