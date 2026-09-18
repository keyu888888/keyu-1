from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from backend.schemas import ErrorCode, Stage, ToolResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def find_binary(name: str) -> Path:
    candidates = list((PROJECT_ROOT / "tools" / "ffmpeg").glob(f"**/{name}.exe"))
    if not candidates:
        raise FileNotFoundError(f"{name}.exe not found under tools/ffmpeg")
    return candidates[0]


def resolve_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path


def probe_video(path: Path) -> dict:
    command = [
        str(find_binary("ffprobe")),
        "-v",
        "error",
        "-show_entries",
        "stream=codec_name,width,height,pix_fmt,r_frame_rate,nb_frames",
        "-show_entries",
        "format=duration,size",
        "-of",
        "json",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(completed.stdout)


def _base_still_filter(zoom: str, x: str, y: str, title: str | None = None) -> str:
    chain = (
        "scale=1600:900:force_original_aspect_ratio=increase,"
        "crop=1600:900,"
        f"zoompan=z='{zoom}':x='{x}':y='{y}':d=96:s=1280x720:fps=24,"
        "setsar=1,trim=duration=4,setpts=PTS-STARTPTS,"
        "fade=t=in:st=0:d=0.35,fade=t=out:st=3.65:d=0.35"
    )
    if title:
        safe_title = title.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:")
        chain += (
            f",drawtext=fontfile='C\\:/Windows/Fonts/msyh.ttc':text='{safe_title}':fontcolor=white:fontsize=52:"
            "box=1:boxcolor=black@0.38:boxborderw=18:"
            "x=(w-text_w)/2:y=h*0.12:enable='between(t,0.4,3.3)'"
        )
    return chain


def compose_final_video(
    hero_image: str | Path,
    core_video: str | Path,
    output_path: str | Path,
    *,
    title: str = "Re Dream",
    music_path: str | Path | None = None,
) -> ToolResult:
    started = time.perf_counter()
    hero_image = resolve_path(hero_image)
    core_video = resolve_path(core_video)
    output_path = resolve_path(output_path)
    music_path = resolve_path(music_path)
    assert hero_image is not None and core_video is not None and output_path is not None
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not hero_image.exists() or not core_video.exists():
        return ToolResult(
            success=False,
            stage=Stage.FINAL_VIDEO_COMPOSED,
            elapsed_s=round(time.perf_counter() - started, 3),
            recoverable=True,
            error_code=ErrorCode.COMPOSE_FAILED,
            message="Hero image or core video is missing",
        )

    filters = [
        f"[0:v]{_base_still_filter('min(zoom+0.0008,1.08)', '(iw-iw/zoom)/2', '(ih-ih/zoom)/2', title)}[v0]",
        f"[0:v]{_base_still_filter('1.08', 'min(on*1.8,iw-iw/zoom)', '(ih-ih/zoom)/2')}[v1]",
        "[1:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
        "fps=24,setsar=1,trim=duration=4,setpts=PTS-STARTPTS,"
        "fade=t=in:st=0:d=0.35,fade=t=out:st=3.65:d=0.35[v2]",
        f"[0:v]{_base_still_filter('min(zoom+0.0006,1.06)', 'iw-iw/zoom', '(ih-ih/zoom)/2')}[v3]",
        f"[0:v]{_base_still_filter('1.06', '(iw-iw/zoom)/2', 'min(on*0.8,ih-ih/zoom)')}[v4]",
        "[v0][v1][v2][v3][v4]concat=n=5:v=1:a=0,"
        "scale=out_range=tv,format=yuv420p,setparams=range=limited[vout]",
    ]

    command = [
        str(find_binary("ffmpeg")),
        "-hide_banner",
        "-loglevel",
        "error",
        "-loop",
        "1",
        "-framerate",
        "24",
        "-i",
        str(hero_image),
        "-i",
        str(core_video),
    ]
    if music_path is not None and music_path.exists():
        command.extend(["-stream_loop", "-1", "-i", str(music_path)])
    command.extend(["-filter_complex", ";".join(filters), "-map", "[vout]"])
    if music_path is not None and music_path.exists():
        command.extend(
            [
                "-map",
                "2:a:0",
                "-af",
                "atrim=duration=20,afade=t=in:st=0:d=1,afade=t=out:st=18:d=2,loudnorm=I=-18:TP=-2:LRA=11",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
            ]
        )
    else:
        command.append("-an")
    command.extend(
        [
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-t",
            "20",
            "-movflags",
            "+faststart",
            "-y",
            str(output_path),
        ]
    )

    completed = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if completed.returncode != 0 or not output_path.exists():
        return ToolResult(
            success=False,
            stage=Stage.FINAL_VIDEO_COMPOSED,
            elapsed_s=round(time.perf_counter() - started, 3),
            recoverable=True,
            error_code=ErrorCode.COMPOSE_FAILED,
            message="FFmpeg composition failed",
            details={"stderr_tail": completed.stderr[-3000:]},
        )

    probe = probe_video(output_path)
    relative_output = output_path.relative_to(PROJECT_ROOT).as_posix()
    return ToolResult(
        success=True,
        stage=Stage.FINAL_VIDEO_COMPOSED,
        artifacts={"final_video": relative_output},
        elapsed_s=round(time.perf_counter() - started, 3),
        recoverable=True,
        message="20-second demo video composed",
        details={"probe": probe},
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hero", required=True)
    parser.add_argument("--core", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", default="Re Dream")
    parser.add_argument("--music")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = compose_final_video(args.hero, args.core, args.output, title=args.title, music_path=args.music)
    print(result.model_dump_json(indent=2))
    if not result.success:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
